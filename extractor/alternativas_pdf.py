"""Recuperacao de alternativas romanas diretamente de PDFs."""

from pathlib import Path

import pymupdf

from extractor.normalizacao_alternativas import (
    normalizar_alternativa_romana,
)


def extrair_grupos_alternativas_romanas(caminho_pdf, numero_pagina):
    """Identifica grupos A-E alinhados e recupera seus textos."""

    caminho = Path(caminho_pdf)

    if not caminho.is_file():
        raise FileNotFoundError(f"PDF nao encontrado: {caminho}")

    with pymupdf.open(caminho) as documento:
        if (
            not isinstance(numero_pagina, int)
            or isinstance(numero_pagina, bool)
            or not 1 <= numero_pagina <= len(documento)
        ):
            raise ValueError("Numero de pagina invalido.")

        pagina = documento[numero_pagina - 1]
        palavras = pagina.get_text("words", sort=True)
        meio = pagina.rect.width / 2

        marcadores = [
            (texto, x0, y0)
            for x0, y0, x1, y1, texto, *_ in palavras
            if texto in {"A", "B", "C", "D", "E"}
        ]

        grupos = []

        for letra, x, y in marcadores:
            if letra != "A":
                continue

            grupo = [(letra, x, y)]

            for esperada in "BCDE":
                anterior_y = grupo[-1][2]

                candidatos = [
                    item
                    for item in marcadores
                    if (
                        item[0] == esperada
                        and abs(item[1] - x) <= 3
                        and 10 <= item[2] - anterior_y <= 35
                    )
                ]

                if not candidatos:
                    break

                grupo.append(
                    min(candidatos, key=lambda item: item[2])
                )

            if len(grupo) != 5:
                continue

            coluna = "esquerda" if x < meio else "direita"
            limite = meio if coluna == "esquerda" else pagina.rect.width

            alternativas = []

            for letra, x_letra, y_letra in grupo:
                partes = [
                    palavra
                    for px0, py0, px1, py1, palavra, *_ in palavras
                    if (
                        x_letra + 8 < px0 < limite
                        and abs(py0 - y_letra) < 3
                    )
                ]

                original = " ".join(partes)

                if not original:
                    raise ValueError(
                        f"Texto ausente na alternativa {letra}."
                    )

                texto = normalizar_alternativa_romana(original)

                alternativas.append({
                    "letra": letra,
                    "texto": texto,
                })

            grupos.append({
                "pagina": numero_pagina,
                "coluna": coluna,
                "posicao_y": y,
                "alternativas": alternativas,
            })

        return sorted(
            grupos,
            key=lambda item: (
                0 if item["coluna"] == "esquerda" else 1,
                item["posicao_y"],
            ),
        )
