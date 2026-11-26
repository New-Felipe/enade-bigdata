"""Recuperacao de alternativas visuais em duas colunas."""
from pathlib import Path
import pymupdf
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
def recuperar_alternativas_visuais_duas_colunas(
    caminho_pdf,
    numero_pagina,
    numero_questao,
    pasta_saida,
):
    """Preserva alternativas visuais A-C e D-E como imagens."""
    if (
        not isinstance(numero_questao, int)
        or isinstance(numero_questao, bool)
        or numero_questao < 1
    ):
        raise ValueError("Numero de questao invalido.")
    grupos = localizar_grupos_alternativas(
        caminho_pdf,
        numero_pagina,
    )
    if len(grupos) != 1:
        raise ValueError(
            "Esperado exatamente um grupo A-E."
        )
    grupo = grupos[0]
    if [item["letra"] for item in grupo] != list("ABCDE"):
        raise ValueError("Sequencia de alternativas invalida.")
    marcadores = {
        item["letra"]: item
        for item in grupo
    }
    a = marcadores["A"]
    b = marcadores["B"]
    c = marcadores["C"]
    d = marcadores["D"]
    e = marcadores["E"]
    layout_valido = (
        abs(a["x"] - b["x"]) <= 3
        and abs(a["x"] - c["x"]) <= 3
        and abs(d["x"] - e["x"]) <= 3
        and d["x"] - a["x"] >= 100
        and abs(a["y"] - d["y"]) <= 5
        and abs(b["y"] - e["y"]) <= 5
    )
    if not layout_valido:
        raise ValueError(
            "Layout de duas colunas nao reconhecido."
        )
    largura_recorte = d["x"] - a["x"] + 2
    pdf = Path(caminho_pdf)
    pasta = Path(pasta_saida) / "imagens"
    alternativas = []
    with pymupdf.open(pdf) as documento:
        pagina = documento[numero_pagina - 1]
        recortes = []
        for letra in "ABCDE":
            marcador = marcadores[letra]
            x = marcador["x"]
            y = marcador["y"]
            area = pymupdf.Rect(
                x - 10,
                y - 85,
                x - 10 + largura_recorte,
                y + 95,
            )
            if (
                area.is_empty
                or not pagina.rect.contains(area)
            ):
                raise ValueError(
                    f"Recorte invalido: alternativa {letra}."
                )
            nome = (
                f"questao_{numero_questao:02d}_{letra}.png"
            )
            recortes.append((letra, area, nome))
        pasta.mkdir(parents=True, exist_ok=True)
        for letra, area, nome in recortes:
            destino = pasta / nome
            pagina.get_pixmap(
                dpi=250,
                clip=area,
                alpha=False,
            ).save(destino)
            alternativas.append({
                "letra": letra,
                "imagem": f"imagens/{nome}",
            })
    return alternativas
