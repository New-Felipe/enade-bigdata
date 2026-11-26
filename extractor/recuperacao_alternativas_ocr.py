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
    coluna=None,
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
    with pymupdf.open(pdf) as documento:
        largura = documento[numero_pagina - 1].rect.width
    centro = largura / 2
    if coluna is None:
        if len(grupos) != 1:
            raise ValueError(
                "Esperado exatamente um grupo A-E na pagina; "
                f"encontrados {len(grupos)}."
            )
        grupo = grupos[0]
    elif coluna in ("esquerda", "direita"):
        candidatos = []
        for candidato in grupos:
            if not candidato:
                continue
            if [
                item.get("letra") for item in candidato
            ] != list("ABCDE"):
                continue
            posicoes = [item.get("x") for item in candidato]
            if not all(
                isinstance(x, (int, float))
                for x in posicoes
            ):
                continue
            pertence = (
                all(x < centro for x in posicoes)
                if coluna == "esquerda"
                else all(x >= centro for x in posicoes)
            )
            if pertence:
                candidatos.append(candidato)
        if len(candidatos) != 1:
            raise ValueError(
                f"Esperado um grupo A-E na coluna {coluna}; "
                f"encontrados {len(candidatos)}."
            )
        grupo = candidatos[0]
    else:
        raise ValueError(
            "Coluna invalida. Use esquerda, direita ou None."
        )
    limite_direito = (
        centro
        if coluna == "esquerda"
        else largura - margem_direita
    )
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
            limite_direito,
            limite_inferior,
        )
        if (
            regiao[0] >= regiao[2]
            or regiao[1] >= regiao[3]
        ):
            raise ValueError(
                f"Recorte invalido para alternativa {letra}."
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
