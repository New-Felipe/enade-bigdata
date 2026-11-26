"""Recuperacao de alternativas textuais usando OCR."""
from pathlib import Path
import pymupdf
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
from extractor.ocr import extrair_regiao_ocr
def recuperar_alternativas_ocr(
    caminho_pdf,
    numero_pagina,
    executavel_tesseract,
    *,
    deslocamento_texto,
    margem_direita,
    altura_ultima,
):
    """Recupera alternativas A-E de um grupo identificado.
    Os parametros de recorte devem ser calibrados para
    o layout do PDF. As medidas usam pontos do documento.
    """
    pdf = Path(caminho_pdf)
    grupos = localizar_grupos_alternativas(
        pdf,
        numero_pagina,
    )
    if len(grupos) != 1:
        raise ValueError(
            "Esperado exatamente um grupo A-E na pagina; "
            f"encontrados {len(grupos)}."
        )
    grupo = grupos[0]
    with pymupdf.open(pdf) as documento:
        largura = documento[numero_pagina - 1].rect.width
    alternativas = []
    for indice, marcador in enumerate(grupo):
        letra = marcador["letra"]
        x = marcador["x"]
        y = marcador["y"]
        if indice < 4:
            limite_inferior = grupo[indice + 1]["y"] - 2
        else:
            limite_inferior = y + altura_ultima
        regiao = (
            x + deslocamento_texto,
            y - 2,
            largura - margem_direita,
            limite_inferior,
        )
        texto = extrair_regiao_ocr(
            caminho_pdf=pdf,
            numero_pagina=numero_pagina,
            regiao=regiao,
            executavel_tesseract=executavel_tesseract,
        )
        texto = " ".join(texto.split())
        if not texto:
            raise ValueError(
                f"Texto ausente na alternativa {letra}."
            )
        alternativas.append({
            "letra": letra,
            "texto": texto,
        })
    return alternativas
