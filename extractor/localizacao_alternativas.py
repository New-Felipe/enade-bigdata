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
                        and 10 <= item[2] - y_anterior <= 75
                    )
                ]
                if not candidatos:
                    break
                grupo.append(
                    min(candidatos, key=lambda item: item[2])
                )
            if len(grupo) != 5:
                continue
            intervalos = [
                grupo[indice + 1][2] - grupo[indice][2]
                for indice in range(4)
            ]

            if max(intervalos) > 1.6 * min(intervalos):
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
        # Caso especial: alternativas A-C na coluna esquerda
        # e alternativas D-E na coluna direita.
        if not grupos and len(marcadores) == 5:
            por_letra = {
                letra: (letra, x, y)
                for letra, x, y in marcadores
            }
            if set(por_letra) == set("ABCDE"):
                a, b, c, d, e = (
                    por_letra[letra]
                    for letra in "ABCDE"
                )
                intervalos = [
                    b[2] - a[2],
                    c[2] - b[2],
                    e[2] - d[2],
                ]
                colunas_validas = (
                    abs(b[1] - a[1]) <= 3
                    and abs(c[1] - a[1]) <= 3
                    and abs(e[1] - d[1]) <= 3
                    and d[1] - a[1] >= 100
                )
                linhas_alinhadas = (
                    abs(d[2] - a[2]) <= 5
                    and abs(e[2] - b[2]) <= 5
                )
                espacamento_valido = (
                    all(75 < valor <= 250 for valor in intervalos)
                    and max(intervalos) <= 1.25 * min(intervalos)
                )
                if (
                    colunas_validas
                    and linhas_alinhadas
                    and espacamento_valido
                ):
                    grupos.append([
                        {
                            "letra": letra,
                            "x": x,
                            "y": y,
                        }
                        for letra, x, y in (
                            a, b, c, d, e
                        )
                    ])
        return grupos
