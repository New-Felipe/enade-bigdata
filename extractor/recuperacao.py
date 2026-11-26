"""Recuperacao dos diagramas da questao 33 do ENADE 2021."""

from copy import deepcopy
from pathlib import Path

import pymupdf


MARCADOR_FINAL = "insere(17, 9)."

# Coordenadas relativas validadas visualmente no PDF original.
RECORTES = {
    "A": (0.05, 0.09, 0.72, 0.27),
    "B": (0.05, 0.27, 0.91, 0.44),
    "C": (0.05, 0.44, 0.62, 0.605),
    "D": (0.05, 0.605, 0.55, 0.780),
    "E": (0.05, 0.780, 0.85, 0.951),
}


def recuperar_questao_33(questao, caminho_pdf, pasta_imagens):
    """Recupera o enunciado e os cinco diagramas originais."""

    if (
        questao.get("numero_questao") != 33
        or questao.get("tipo_questao") != "objetiva"
        or questao.get("origem", {}).get("pagina") != 36
        or questao.get("pagina_final") != 37
    ):
        raise ValueError("Documento nao corresponde a questao 33 esperada.")

    texto = questao.get("texto", "")

    if texto.count(MARCADOR_FINAL) != 1:
        raise ValueError("Fim do enunciado nao identificado.")

    pdf = Path(caminho_pdf)

    if not pdf.is_file():
        raise FileNotFoundError(f"PDF nao encontrado: {pdf}")

    pasta = Path(pasta_imagens)
    recuperada = deepcopy(questao)

    recuperada["texto"] = (
        texto.split(MARCADOR_FINAL, 1)[0] + MARCADOR_FINAL
    )

    recuperada["alternativas"] = []

    with pymupdf.open(pdf) as documento:
        if len(documento) < 37:
            raise ValueError("PDF nao possui a pagina 37.")

        pagina = documento[36]
        largura = pagina.rect.width
        altura = pagina.rect.height

        pasta.mkdir(parents=True, exist_ok=True)

        for letra, coordenadas in RECORTES.items():
            x0, y0, x1, y1 = coordenadas

            area = pymupdf.Rect(
                largura * x0,
                altura * y0,
                largura * x1,
                altura * y1,
            )

            nome = f"questao_33_{letra}.png"
            destino = pasta / nome

            imagem = pagina.get_pixmap(
                dpi=220,
                clip=area,
                alpha=False,
            )
            imagem.save(destino)

            recuperada["alternativas"].append({
                "letra": letra,
                "imagem": f"imagens/{nome}",
            })

    return recuperada
