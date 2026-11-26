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

def anexar_imagem_incorporada_enunciado(
    questao,
    caminho_pdf,
    pasta_saida,
    nome_arquivo,
):
    """Anexa uma imagem incorporada preservando sua resolucao."""
    from copy import deepcopy
    from pathlib import Path
    import pymupdf
    pdf = Path(caminho_pdf)
    if not pdf.is_file():
        raise FileNotFoundError(
            f"PDF nao encontrado: {pdf}"
        )
    numero_pagina = questao["origem"]["pagina"]
    if (
        not isinstance(numero_pagina, int)
        or isinstance(numero_pagina, bool)
        or numero_pagina < 1
    ):
        raise ValueError("Numero de pagina invalido.")
    nome = Path(nome_arquivo)
    if (
        nome.name != nome_arquivo
        or nome.suffix.lower() != ".png"
    ):
        raise ValueError(
            "O nome da imagem deve ser um arquivo PNG simples."
        )
    with pymupdf.open(pdf) as documento:
        if numero_pagina > len(documento):
            raise ValueError(
                "Pagina da questao nao existe no PDF."
            )
        pagina = documento[numero_pagina - 1]
        xrefs = sorted({
            imagem[0]
            for imagem in pagina.get_images(full=True)
            if pagina.get_image_rects(imagem[0])
        })
        if len(xrefs) != 1:
            raise ValueError(
                "Esperada exatamente uma imagem incorporada "
                f"na pagina; encontradas {len(xrefs)}."
            )
        imagem = pymupdf.Pixmap(documento, xrefs[0])
        # Converte CMYK para RGB quando necessario.
        if imagem.n - imagem.alpha > 3:
            imagem = pymupdf.Pixmap(
                pymupdf.csRGB,
                imagem,
            )
        pasta_imagens = Path(pasta_saida) / "imagens"
        pasta_imagens.mkdir(parents=True, exist_ok=True)
        destino = pasta_imagens / nome_arquivo
        imagem.save(str(destino))
    recuperada = deepcopy(questao)
    referencia = f"imagens/{nome_arquivo}"
    imagens = recuperada.setdefault(
        "imagens_enunciado",
        [],
    )
    if referencia not in imagens:
        imagens.append(referencia)
    return recuperada
