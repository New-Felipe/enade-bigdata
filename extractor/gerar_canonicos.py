"""Gera JSONs canonicos a partir das questoes ENADE 2021."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from extractor.associacao_gabarito import associar_gabarito
from extractor.conversor import converter_questao_canonica
from extractor.extractor import extrair_paginas
from extractor.gabarito import interpretar_gabarito
from scripts.validar_modelo import CAMINHO_SCHEMA, validar_documento


BASE = Path("data/processed/enade/2021/sistemas_de_informacao")

ENTRADA = BASE / "questoes"
SAIDA = BASE / "questoes_canonicas"
RELATORIO = BASE / "relatorio_processamento.json"

GABARITO_PDF = Path(
    "data/raw/enade/2021/sistemas_de_informacao/"
    "enade_2021_sistemas_de_informacao_gabarito.pdf"
)


def main():
    arquivos = sorted(ENTRADA.glob("*.json"))

    if len(arquivos) != 40:
        raise RuntimeError(
            f"Esperadas 40 questoes intermediarias; encontradas {len(arquivos)}."
        )

    paginas = extrair_paginas(str(GABARITO_PDF))
    texto = "\n".join(pagina["texto"] for pagina in paginas)
    registros = interpretar_gabarito(texto)

    schema = json.loads(
        CAMINHO_SCHEMA.read_text(encoding="utf-8")
    )
    validador = Draft202012Validator(schema)

    aprovadas = {}
    pendentes = []

    for arquivo in arquivos:
        questao = json.loads(arquivo.read_text(encoding="utf-8"))

        status = questao.get("validacao_extracao", {}).get("status")

        if status != "extraido_textualmente":
            pendentes.append({
                "arquivo": arquivo.name,
                "motivo": f"Extracao: {status}",
            })
            continue

        try:
            associada = associar_gabarito(questao, registros)
            documento = converter_questao_canonica(associada, 2021)
            erros = validar_documento(validador, documento)

            if erros:
                pendentes.append({
                    "arquivo": arquivo.name,
                    "motivo": "; ".join(erros),
                })
                continue

            identificador = documento["id"]

            if identificador in aprovadas:
                raise RuntimeError(
                    f"Identificador canonico duplicado: {identificador}"
                )

            aprovadas[identificador] = documento

        except (ValueError, KeyError, TypeError) as erro:
            pendentes.append({
                "arquivo": arquivo.name,
                "motivo": str(erro),
            })

    # So inicia a exportacao apos analisar todas as questoes.
    SAIDA.mkdir(parents=True, exist_ok=True)

    for identificador, documento in sorted(aprovadas.items()):
        caminho = SAIDA / f"{identificador}.json"
        caminho.write_text(
            json.dumps(documento, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    relatorio = {
        "ano": 2021,
        "curso": "Sistemas de Informação",
        "total_analisado": len(arquivos),
        "total_aprovado": len(aprovadas),
        "total_pendente": len(pendentes),
        "pendentes": pendentes,
    }

    RELATORIO.write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Questoes analisadas: {len(arquivos)}")
    print(f"JSONs canonicos gerados: {len(aprovadas)}")
    print(f"Pendentes de revisao: {len(pendentes)}")
    print(f"Diretorio de saida: {SAIDA}")
    print(f"Relatorio: {RELATORIO}")


if __name__ == "__main__":
    main()
