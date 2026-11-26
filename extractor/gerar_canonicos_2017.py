"""Gera questoes canonicas a partir do ENADE 2017."""
import json
import shutil
from pathlib import Path
from jsonschema import Draft202012Validator
from extractor.associacao_gabarito import associar_gabarito
from extractor.conversor import converter_questao_canonica
from extractor.extractor import extrair_paginas
from extractor.gabarito import interpretar_gabarito
from scripts.validar_modelo import CAMINHO_SCHEMA, validar_documento
BASE = Path("data/processed/enade/2017/sistemas_de_informacao")
ENTRADA = BASE / "questoes"
SAIDA = BASE / "questoes_canonicas"
RELATORIO = BASE / "relatorio_processamento.json"
GABARITO_PDF = Path(
    "data/raw/enade/2017/sistemas_de_informacao/"
    "enade_2017_sistemas_de_informacao_gabarito.pdf"
)
def main(gravar=False):
    """Valida os 40 canonicos; grava somente quando autorizado."""
    arquivos = sorted(ENTRADA.glob("*.json"))
    esperados = {
        f"objetiva_{numero:02d}.json"
        for numero in range(1, 36)
    } | {
        f"discursiva_{numero:02d}.json"
        for numero in range(1, 6)
    }
    encontrados = {arquivo.name for arquivo in arquivos}
    if encontrados != esperados:
        raise RuntimeError(
            f"Conjunto de questoes incompleto. "
            f"Ausentes: {sorted(esperados - encontrados)}; "
            f"Inesperados: {sorted(encontrados - esperados)}"
        )
    paginas = extrair_paginas(str(GABARITO_PDF))
    texto_gabarito = "\n".join(
        pagina["texto"] for pagina in paginas
    )
    registros = interpretar_gabarito(texto_gabarito)
    chaves_objetivas = {
        ("objetiva", numero)
        for numero in range(1, 36)
    }
    if set(registros) != chaves_objetivas:
        raise RuntimeError("Gabarito objetivo de 2017 incompleto.")
    if registros[("objetiva", 14)] != {
        "gabarito": None,
        "anulada": True,
    }:
        raise RuntimeError("Anulacao da objetiva 14 incorreta.")
    # O PDF oficial nao fornece gabaritos discursivos.
    for numero in range(1, 6):
        registros[("discursiva", numero)] = {
            "gabarito": None,
            "anulada": False,
        }
    schema = json.loads(
        CAMINHO_SCHEMA.read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    validador = Draft202012Validator(schema)
    canonicos = {}
    referencias = set()
    for arquivo in arquivos:
        questao = json.loads(
            arquivo.read_text(encoding="utf-8")
        )
        tipo = questao["tipo_questao"]
        numero = questao["numero_questao"]
        if arquivo.name != f"{tipo}_{numero:02d}.json":
            raise RuntimeError(
                f"Identificacao inconsistente: {arquivo.name}"
            )
        status = questao.get(
            "validacao_extracao", {}
        ).get("status")
        if status not in (
            "extraido_textualmente",
            "recuperado_com_imagens",
        ):
            raise RuntimeError(
                f"Questao pendente: {arquivo.name} ({status})"
            )
        associada = associar_gabarito(questao, registros)
        documento = converter_questao_canonica(
            associada, 2017
        )
        erros = validar_documento(validador, documento)
        if erros:
            raise RuntimeError(
                f"Schema invalido em {arquivo.name}: "
                + "; ".join(erros)
            )
        identificador = documento["id"]
        if identificador in canonicos:
            raise RuntimeError(
                f"Identificador duplicado: {identificador}"
            )
        canonicos[identificador] = documento
        referencias.update(
            documento.get("imagens_enunciado", [])
        )
        referencias.update(
            alternativa["imagem"]
            for alternativa in documento["alternativas"]
            if "imagem" in alternativa
        )
    # Verifica todas as imagens antes de gravar arquivos.
    copias = []
    for referencia in sorted(referencias):
        relativo = Path(referencia)
        if (
            relativo.is_absolute()
            or len(relativo.parts) != 2
            or relativo.parts[0] != "imagens"
            or relativo.name in (".", "..")
        ):
            raise RuntimeError(
                f"Referencia de imagem invalida: {referencia}"
            )
        origem = ENTRADA / relativo
        destino = SAIDA / relativo
        if destino.is_file() and destino.stat().st_size > 0:
            if (
                origem.is_file()
                and origem.read_bytes() != destino.read_bytes()
            ):
                raise RuntimeError(
                    f"Imagens divergentes: {referencia}"
                )
            continue
        if not origem.is_file() or origem.stat().st_size == 0:
            raise RuntimeError(
                f"Imagem nao encontrada: {referencia}"
            )
        copias.append((origem, destino))
    print("\nENADE 2017 - GERACAO CANONICA")
    print("=" * 55)
    print("Questoes analisadas:", len(arquivos))
    print("Canonicos validados:", len(canonicos))
    print("Imagens verificadas:", len(referencias))
    print("Imagens a copiar:", len(copias))
    if gravar:
        SAIDA.mkdir(parents=True, exist_ok=True)
        for origem, destino in copias:
            destino.parent.mkdir(
                parents=True, exist_ok=True
            )
            shutil.copy2(origem, destino)
        for identificador, documento in sorted(
            canonicos.items()
        ):
            destino = SAIDA / f"{identificador}.json"
            destino.write_text(
                json.dumps(
                    documento,
                    ensure_ascii=False,
                    indent=2,
                ) + "\n",
                encoding="utf-8",
            )
        relatorio = {
            "ano": 2017,
            "curso": "Sistemas de Informação",
            "total_analisado": len(arquivos),
            "total_aprovado": len(canonicos),
            "total_pendente": 0,
            "pendentes": [],
        }
        RELATORIO.write_text(
            json.dumps(
                relatorio,
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        print("JSONs canonicos gravados:", len(canonicos))
        print("Relatorio:", RELATORIO)
    else:
        print("Modo: SIMULACAO")
        print("Nenhum JSON canonico foi gravado.")
    print("Diretorio:", SAIDA)
if __name__ == "__main__":
    main()
