"""Recuperacao de conteudos visuais dos enunciados ENADE."""
from copy import deepcopy
from pathlib import Path
import pymupdf
def anexar_imagem_enunciado(
    questao,
    caminho_pdf,
    pasta_saida,
    recorte,
    nome_arquivo,
):
    """Extrai uma imagem do PDF e a associa ao enunciado."""
    pdf = Path(caminho_pdf)
    pasta = Path(pasta_saida)
    if not pdf.is_file():
        raise FileNotFoundError(f"PDF nao encontrado: {pdf}")
    nome = Path(nome_arquivo)
    if (
        not isinstance(nome_arquivo, str)
        or nome.name != nome_arquivo
        or nome.suffix.lower() != ".png"
    ):
        raise ValueError("Nome de arquivo PNG invalido.")
    numero_pagina = questao.get("origem", {}).get("pagina")
    if (
        type(numero_pagina) is not int
        or numero_pagina < 1
    ):
        raise ValueError("Pagina de origem invalida.")
    try:
        area = pymupdf.Rect(recorte)
    except (TypeError, ValueError) as erro:
        raise ValueError("Recorte invalido.") from erro
    with pymupdf.open(pdf) as documento:
        if numero_pagina > len(documento):
            raise ValueError("Pagina fora dos limites do PDF.")
        pagina = documento[numero_pagina - 1]
        if (
            area.is_empty
            or not pagina.rect.contains(area)
        ):
            raise ValueError(
                "Recorte fora dos limites da pagina."
            )
        imagem = pagina.get_pixmap(
            dpi=300,
            clip=area,
            alpha=False,
        )
        destino = pasta / "imagens" / nome_arquivo
        destino.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        imagem.save(destino)
    recuperada = deepcopy(questao)
    referencia = f"imagens/{nome_arquivo}"
    imagens = recuperada.setdefault(
        "imagens_enunciado", []
    )
    if referencia not in imagens:
        imagens.append(referencia)
    return recuperada
