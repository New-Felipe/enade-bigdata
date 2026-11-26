"""Recuperacao OCR de questoes objetivas textuais."""
from pathlib import Path
import pymupdf
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
from extractor.normalizacao_ocr import normalizar_quebras_ocr
from extractor.ocr import extrair_regiao_ocr
from extractor.recuperacao_alternativas_ocr import (
    recuperar_alternativas_ocr,
)
from extractor.segmenter import identificar_titulo_ocr
def recuperar_questao_textual_ocr(
    plano,
    caminho_pdf,
    arquivo_origem,
    executavel_tesseract,
    altura_ultima=25,
):
    """Recupera uma questao objetiva textual de pagina unica."""
    pdf = Path(caminho_pdf)
    if not pdf.is_file():
        raise FileNotFoundError(
            f"PDF nao encontrado: {pdf}"
        )
    numero = plano["numero_questao"]
    tipo = plano["tipo_questao"]
    pagina_numero = plano["pagina_inicial"]
    if tipo != "objetiva":
        raise ValueError(
            "O recuperador textual aceita apenas objetivas."
        )
    if plano["pagina_final_candidata"] != pagina_numero:
        raise ValueError(
            "A questao deve ocupar uma unica pagina."
        )
    if (
        not isinstance(pagina_numero, int)
        or isinstance(pagina_numero, bool)
        or pagina_numero < 1
    ):
        raise ValueError("Numero de pagina invalido.")
    grupos = localizar_grupos_alternativas(
        pdf,
        pagina_numero,
    )
    with pymupdf.open(pdf) as documento:
        if pagina_numero > len(documento):
            raise ValueError(
                "Pagina inexistente no PDF."
            )
        pagina = documento[pagina_numero - 1]
        limites = pymupdf.Rect(pagina.rect)
        # Evita descartar silenciosamente figuras incorporadas.
        imagens = [
            xref
            for item in pagina.get_images(full=True)
            if (xref := item[0])
            and pagina.get_image_rects(xref)
        ]
        if imagens:
            raise ValueError(
                "Pagina contem imagem incorporada; "
                "utilize o recuperador visual."
            )
    coluna = plano.get("coluna")
    if coluna not in (None, "esquerda", "direita"):
        raise ValueError(
            "Coluna invalida no plano de extracao."
        )
    centro = limites.width / 2
    if coluna is None:
        # Mantem o comportamento de pagina inteira.
        candidatos = grupos
    else:
        candidatos = []
        for grupo in grupos:
            if not grupo:
                continue
            posicoes = [
                alternativa.get("x")
                for alternativa in grupo
            ]
            if not all(
                isinstance(x, (int, float))
                for x in posicoes
            ):
                continue
            if coluna == "esquerda":
                corresponde = all(
                    x < centro for x in posicoes
                )
            else:
                corresponde = all(
                    x >= centro for x in posicoes
                )
            if corresponde:
                candidatos.append(grupo)
    if (
        len(candidatos) != 1
        or [
            alternativa.get("letra")
            for alternativa in candidatos[0]
        ] != list("ABCDE")
    ):
        raise ValueError(
            "Nao foi encontrado um grupo A-E unico "
            "para a coluna da questao."
        )
    grupo = candidatos[0]
    y_alternativa_a = grupo[0]["y"]
    limite_esquerdo = (
        centro if coluna == "direita" else 25
    )
    limite_direito = (
        centro
        if coluna == "esquerda"
        else limites.width - 25
    )
    regiao = (
        limite_esquerdo,
        65,
        limite_direito,
        y_alternativa_a - 5,
    )
    area = pymupdf.Rect(regiao)
    if area.is_empty or not limites.contains(area):
        raise ValueError(
            "Regiao do enunciado invalida."
        )
    texto_ocr = extrair_regiao_ocr(
        caminho_pdf=pdf,
        numero_pagina=pagina_numero,
        regiao=regiao,
        executavel_tesseract=executavel_tesseract,
        dpi=300,
        psm=4,
    )
    linhas = texto_ocr.splitlines()
    titulos = [
        (indice, titulo)
        for indice, linha in enumerate(linhas)
        if (titulo := identificar_titulo_ocr(linha))
    ]
    esperado = {
        "numero_questao": numero,
        "tipo_questao": tipo,
    }
    if (
        len(titulos) != 1
        or titulos[0][1] != esperado
    ):
        raise ValueError(
            "Titulo OCR nao corresponde ao plano."
        )
    texto = normalizar_quebras_ocr(
        "\n".join(linhas[titulos[0][0] + 1:])
    )
    if not texto:
        raise ValueError(
            "Enunciado vazio apos o OCR."
        )
    alternativas = recuperar_alternativas_ocr(
        caminho_pdf=pdf,
        numero_pagina=pagina_numero,
        executavel_tesseract=executavel_tesseract,
        deslocamento_texto=18,
        margem_direita=35,
        altura_ultima=altura_ultima,
        coluna=coluna,
    )
    if (
        [a["letra"] for a in alternativas] != list("ABCDE")
        or any(
            not a.get("texto", "").strip()
            for a in alternativas
        )
    ):
        raise ValueError(
            "Alternativas incompletas ou invalidas."
        )
    return {
        "numero_questao": numero,
        "tipo_questao": tipo,
        "texto": texto,
        "alternativas": alternativas,
        "origem": {
            "arquivo": arquivo_origem,
            "pagina": pagina_numero,
        },
        "pagina_final": pagina_numero,
    }
