"""Localizacao de marcadores de alternativas em PDFs."""
from pathlib import Path
import pymupdf
def localizar_grupos_alternativas(caminho_pdf, numero_pagina):
    """Localiza sequencias A-E alinhadas em uma pagina."""
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
        marcadores = sorted(
            [
                (texto, x0, y0)
                for x0, y0, x1, y1, texto, *_ in palavras
                if texto in {"A", "B", "C", "D", "E"}
            ],
            key=lambda item: (item[2], item[1]),
        )
        grupos = []
        assinaturas = set()
        for marcador in marcadores:
            if marcador[0] != "A":
                continue
            grupo = [marcador]
            x_referencia = marcador[1]
            for letra_esperada in "BCDE":
                y_anterior = grupo[-1][2]
                candidatos = [
                    item
                    for item in marcadores
                    if (
                        item[0] == letra_esperada
                        and abs(item[1] - x_referencia) <= 3
                        and 10 <= item[2] - y_anterior <= 45
                    )
                ]
                if not candidatos:
                    break
                grupo.append(
                    min(candidatos, key=lambda item: item[2])
                )
            if len(grupo) != 5:
                continue
            assinatura = tuple(grupo)
            if assinatura in assinaturas:
                continue
            assinaturas.add(assinatura)
            grupos.append([
                {
                    "letra": letra,
                    "x": x,
                    "y": y,
                }
                for letra, x, y in grupo
            ])
        return grupos
