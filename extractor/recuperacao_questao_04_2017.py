"""Recuperacao integrada da questao 04 do ENADE 2017."""
from pathlib import Path
import pymupdf
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
from extractor.ocr import extrair_regiao_ocr
from extractor.recuperacao_alternativas_ocr import (
    recuperar_alternativas_ocr,
)
from extractor.recuperacao_imagens_enunciado import (
    anexar_imagem_enunciado,
)
from extractor.segmenter import identificar_titulo_ocr
NUMERO_QUESTAO = 4
NUMERO_PAGINA = 8
# Regioes verificadas no PDF oficial de 2017.
REGIAO_TIRINHA = (55, 148, 573, 318)
def recuperar_questao_04_2017(
    caminho_pdf,
    executavel_tesseract,
    pasta_saida,
):
    """Recupera o enunciado, a tirinha e as alternativas A-E."""
    pdf = Path(caminho_pdf)
    if not pdf.is_file():
        raise FileNotFoundError(
            f"PDF nao encontrado: {pdf}"
        )
    grupos = localizar_grupos_alternativas(
        pdf,
        NUMERO_PAGINA,
    )
    if (
        len(grupos) != 1
        or [item["letra"] for item in grupos[0]] != list("ABCDE")
    ):
        raise ValueError(
            "Alternativas da questao 04 nao localizadas."
        )
    y_alternativa_a = grupos[0][0]["y"]
    with pymupdf.open(pdf) as documento:
        if len(documento) < NUMERO_PAGINA:
            raise ValueError(
                "PDF nao possui a pagina da questao 04."
            )
        limites = pymupdf.Rect(
            documento[NUMERO_PAGINA - 1].rect
        )
    regioes = {
        "superior": (
            25, 80, limites.width - 25, 147
        ),
        "inferior": (
            25,
            318,
            limites.width - 25,
            y_alternativa_a - 5,
        ),
    }
    textos = {}
    for nome, regiao in regioes.items():
        area = pymupdf.Rect(regiao)
        if area.is_empty or not limites.contains(area):
            raise ValueError(
                f"Regiao OCR invalida: {nome}."
            )
        textos[nome] = extrair_regiao_ocr(
            caminho_pdf=pdf,
            numero_pagina=NUMERO_PAGINA,
            regiao=regiao,
            executavel_tesseract=executavel_tesseract,
            dpi=300,
            psm=4,
        )
    linhas_superiores = textos["superior"].splitlines()
    titulos = [
        (indice, titulo)
        for indice, linha in enumerate(linhas_superiores)
        if (titulo := identificar_titulo_ocr(linha))
    ]
    if (
        len(titulos) != 1
        or titulos[0][1] != {
            "numero_questao": NUMERO_QUESTAO,
            "tipo_questao": "objetiva",
        }
    ):
        raise ValueError(
            "Titulo da questao 04 nao identificado corretamente."
        )
    inicio = titulos[0][0] + 1
    texto_superior = "\n".join(
        linhas_superiores[inicio:]
    ).strip()
    texto_inferior = textos["inferior"].strip()
    if (
        not texto_superior
        or "TEXTO 1" not in texto_superior
        or "TEXTO 2" not in texto_inferior
    ):
        raise ValueError(
            "Enunciado da questao 04 incompleto."
        )
    alternativas = recuperar_alternativas_ocr(
        caminho_pdf=pdf,
        numero_pagina=NUMERO_PAGINA,
        executavel_tesseract=executavel_tesseract,
        deslocamento_texto=18,
        margem_direita=35,
        altura_ultima=40,
    )
    if (
        [item["letra"] for item in alternativas] != list("ABCDE")
        or any(
            not item.get("texto", "").strip()
            for item in alternativas
        )
    ):
        raise ValueError(
            "Alternativas da questao 04 incompletas."
        )
    questao = {
        "numero_questao": NUMERO_QUESTAO,
        "tipo_questao": "objetiva",
        "texto": (
            texto_superior
            + "\n\n"
            + texto_inferior
        ),
        "alternativas": alternativas,
        "origem": {
            "arquivo": pdf.name,
            "pagina": NUMERO_PAGINA,
        },
        "pagina_final": NUMERO_PAGINA,
    }
    return anexar_imagem_enunciado(
        questao=questao,
        caminho_pdf=pdf,
        pasta_saida=pasta_saida,
        recorte=REGIAO_TIRINHA,
        nome_arquivo="questao_04_tirinha.png",
    )
