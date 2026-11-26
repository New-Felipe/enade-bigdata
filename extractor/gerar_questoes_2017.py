"""Gera JSONs intermediarios da prova ENADE 2017."""
from functools import partial
from pathlib import Path
from extractor.extractor import extrair_paginas
from extractor.recuperacao_alternativas_visuais import (
    recuperar_alternativas_visuais_duas_colunas,
)
from extractor.recuperacao_discursivas_2017 import (
    recuperar_discursiva_04_2017,
    recuperar_discursiva_05_2017,
)
from extractor.gerador_json import salvar_questoes_json
from extractor.recuperacao_objetivas_especiais_2017 import (
    recuperar_questao_04_2017,
    recuperar_questao_21_2017,
)
from extractor.recuperacao_questao_imagem import (
    recuperar_questao_com_imagem_incorporada,
)
from extractor.recuperacao_questao_textual_ocr import (
    recuperar_questao_textual_ocr,
)
from extractor.revisoes_manuais_2017 import (
    revisar_alternativas_2017,
    revisar_enunciado_2017,
)
from extractor.segmenter import (
    extrair_questoes_planejadas,
    mapear_questoes_prova,
    planejar_extracao_questoes,
)
PDF = Path(
    "data/raw/enade/2017/sistemas_de_informacao/"
    "enade_2017_sistemas_de_informacao_prova.pdf"
)
BASE = Path(
    "data/processed/enade/2017/sistemas_de_informacao"
)
SAIDA = BASE / "questoes"
IMAGENS = SAIDA / "imagens"
def recuperar_questao_2017(
    plano,
    caminho_pdf,
    arquivo_origem,
    executavel_tesseract,
    pasta_saida,
):
    """Seleciona a recuperacao adequada para as questoes de 2017."""
    if (
        plano["tipo_questao"] == "discursiva"
        and plano["numero_questao"] == 4
    ):
        return recuperar_discursiva_04_2017(
            plano=plano,
            caminho_pdf=caminho_pdf,
            arquivo_origem=arquivo_origem,
            executavel_tesseract=executavel_tesseract,
            pasta_saida=pasta_saida,
        )
    if (
        plano["tipo_questao"] == "discursiva"
        and plano["numero_questao"] == 5
    ):
        return recuperar_discursiva_05_2017(
            plano=plano,
            caminho_pdf=caminho_pdf,
            arquivo_origem=arquivo_origem,
            executavel_tesseract=executavel_tesseract,
            pasta_saida=pasta_saida,
        )
    if plano["tipo_questao"] != "objetiva":
        raise ValueError(
            "Recuperacao OCR de discursivas ainda nao implementada."
        )
    numero = plano["numero_questao"]
    if numero == 21:
        # A questao 21 continua na pagina 27, antes da questao 22.
        # Ajusta apenas uma copia do plano original.
        plano_21 = dict(plano)
        plano_21["pagina_final_candidata"] = 27
        plano_21["multiplas_paginas"] = True
        return recuperar_questao_21_2017(
            plano=plano_21,
            caminho_pdf=caminho_pdf,
            arquivo_origem=arquivo_origem,
            executavel_tesseract=executavel_tesseract,
            pasta_saida=pasta_saida,
        )
    if numero == 4:
        questao = recuperar_questao_04_2017(
            caminho_pdf=caminho_pdf,
            executavel_tesseract=executavel_tesseract,
            pasta_saida=pasta_saida,
        )
    elif numero == 5:
        questao = recuperar_questao_com_imagem_incorporada(
            plano=plano,
            caminho_pdf=caminho_pdf,
            arquivo_origem=arquivo_origem,
            executavel_tesseract=executavel_tesseract,
            pasta_saida=pasta_saida,
            altura_ultima=25,
        )
    else:
        plano_ocr = plano
        altura_ultima = 25
        if numero == 35:
            # A ultima objetiva termina na pagina 35.
            # O planejamento original nao deve ser alterado.
            plano_ocr = dict(plano)
            plano_ocr["pagina_final_candidata"] = 35
            plano_ocr["multiplas_paginas"] = False
            altura_ultima = 60
        questao = recuperar_questao_textual_ocr(
            plano=plano_ocr,
            caminho_pdf=caminho_pdf,
            arquivo_origem=arquivo_origem,
            executavel_tesseract=executavel_tesseract,
            altura_ultima=altura_ultima,
        )
    if numero in (14, 15):
        questao = revisar_alternativas_2017(questao)
        questao = revisar_enunciado_2017(questao)
        if numero == 15:
            auditoria = questao.get("revisao_manual", {})
            if not all(
                campo in auditoria
                for campo in ("alternativas_ocr", "texto_ocr")
            ):
                raise ValueError(
                    "Revisao da questao 15 incompleta; "
                    "verifique o resultado do OCR."
                )
    return questao
def main(
    executavel_tesseract=(
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    ),
):
    """Mapeia, recupera e exporta questoes intermediarias."""
    paginas = extrair_paginas(PDF)
    mapeadas = mapear_questoes_prova(
        paginas,
        str(PDF),
        executavel_tesseract=executavel_tesseract,
    )
    if len(mapeadas) != 40:
        raise RuntimeError(
            f"Mapeamento incompleto: {len(mapeadas)}/40 questoes."
        )
    planos = planejar_extracao_questoes(
        mapeadas,
        len(paginas),
    )
    recuperador = partial(
        recuperar_questao_2017,
        executavel_tesseract=executavel_tesseract,
        pasta_saida=IMAGENS,
    )
    resultado = extrair_questoes_planejadas(
        paginas=paginas,
        planos=planos,
        caminho_pdf=str(PDF),
        arquivo_origem=PDF.name,
        recuperador_ocr=recuperador,
        priorizar_ocr=True,
    )
    extraidas = resultado["extraidas"]
    falhas = resultado["falhas"]
    revisar = resultado["revisar"]
    # Recupera as alternativas visuais da objetiva 20.
    pendente_20 = any(
        item["tipo_questao"] == "objetiva"
        and item["numero_questao"] == 20
        for item in revisar
    )
    if pendente_20:
        encontradas = [
            questao for questao in extraidas
            if questao["tipo_questao"] == "objetiva"
            and questao["numero_questao"] == 20
        ]
        if len(encontradas) != 1:
            raise RuntimeError(
                "Objetiva 20 nao encontrada de forma unica."
            )
        questao_20 = encontradas[0]
        if questao_20["origem"]["pagina"] != 25:
            raise RuntimeError(
                "Pagina inesperada para a objetiva 20."
            )
        alternativas = (
            recuperar_alternativas_visuais_duas_colunas(
                caminho_pdf=PDF,
                numero_pagina=25,
                numero_questao=20,
                pasta_saida=SAIDA,
            )
        )
        if (
            len(alternativas) != 5
            or [a["letra"] for a in alternativas] != list("ABCDE")
            or not all(a.get("imagem") for a in alternativas)
        ):
            raise RuntimeError(
                "Alternativas visuais da objetiva 20 invalidas."
            )
        questao_20["alternativas"] = alternativas
        revisar = [
            item for item in revisar
            if not (
                item["tipo_questao"] == "objetiva"
                and item["numero_questao"] == 20
            )
        ]
    if falhas or revisar or len(extraidas) != 40:
        detalhes = [
            f"{item['tipo_questao']} "
            f"{item['numero_questao']:02d}: "
            f"{item.get('erro', item.get('motivo', 'Pendente'))}"
            for item in falhas + revisar
        ]
        mensagem = (
            f"Extracao incompleta: {len(extraidas)}/40 questoes; "
            f"{len(falhas)} falhas; "
            f"{len(revisar)} pendencias de revisao."
        )
        if detalhes:
            mensagem += "\n" + "\n".join(detalhes)
        raise RuntimeError(mensagem)
    arquivos = salvar_questoes_json(
        extraidas,
        SAIDA,
    )
    print("ENADE 2017 - QUESTOES INTERMEDIARIAS")
    print("=" * 55)
    print(f"Questoes extraidas: {len(extraidas)}")
    print(f"JSONs gerados: {len(arquivos)}")
    print(f"Diretorio: {SAIDA}")
if __name__ == "__main__":
    main()
