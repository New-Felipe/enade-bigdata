"""Funcoes de extracao textual de provas em PDF."""

import re
from pathlib import Path

import pymupdf


def extrair_paginas(caminho_pdf):
    """Extrai texto por pagina, preservando o numero original."""
    caminho = Path(caminho_pdf)

    if not caminho.is_file():
        raise FileNotFoundError(f"PDF nao encontrado: {caminho}")

    paginas = []

    with pymupdf.open(caminho) as documento:
        for numero, pagina in enumerate(documento, start=1):
            paginas.append({
                "pagina": numero,
                "texto": pagina.get_text("text", sort=True),
            })

    return paginas


def extrair_colunas(caminho_pdf, numero_pagina):
    """Extrai separadamente as metades esquerda e direita."""
    caminho = Path(caminho_pdf)

    if not caminho.is_file():
        raise FileNotFoundError(f"PDF nao encontrado: {caminho}")

    with pymupdf.open(caminho) as documento:
        if not 1 <= numero_pagina <= len(documento):
            raise ValueError("Numero de pagina invalido.")

        pagina = documento[numero_pagina - 1]
        meio = pagina.rect.width / 2

        areas = {
            "esquerda": pymupdf.Rect(
                0, 0, meio, pagina.rect.height
            ),
            "direita": pymupdf.Rect(
                meio, 0, pagina.rect.width, pagina.rect.height
            ),
        }

        return {
            "pagina": numero_pagina,
            "colunas": {
                nome: pagina.get_text("text", clip=area, sort=True)
                for nome, area in areas.items()
            },
        }

def limpar_texto_pagina(texto, numero_pagina, coluna=None):
    """Remove identificadores e rodapes conhecidos das provas ENADE."""
    if coluna not in (None, "esquerda", "direita"):
        raise ValueError("Nome de coluna invalido.")

    linhas = texto.splitlines()
    linhas_limpas = []

    padrao_identificador = re.compile(r"^\*R\d{7,}\*$")

    padrao_rodape = re.compile(
        r"^(?:\d+\s+Sistemas de informa.+|"
        r"Sistemas de informa.+\s+\d+)$",
        re.IGNORECASE,
    )

    # Fragmentos de rodape gerados pela divisao em duas colunas.
    padrao_rodape_direita_impar = re.compile(
        rf"^informa(?:ção|cao)\s+{numero_pagina}$",
        re.IGNORECASE,
    )
    padrao_rodape_esquerda_par = re.compile(
        rf"^{numero_pagina}\s+Sistemas de$",
        re.IGNORECASE,
    )
    padrao_rodape_esquerda_impar = re.compile(
        r"^Sistemas de$",
        re.IGNORECASE,
    )
    padrao_rodape_direita_par = re.compile(
        r"^informa(?:ção|cao)$",
        re.IGNORECASE,
    )

    ultima_linha = max(
        (i for i, linha in enumerate(linhas) if linha.strip()),
        default=-1,
    )
    linha_anterior_vazia = (
        ultima_linha > 0 and not linhas[ultima_linha - 1].strip()
    )
    pagina_par = numero_pagina % 2 == 0

    for indice, linha in enumerate(linhas):
        conteudo = linha.strip()

        if padrao_identificador.fullmatch(conteudo):
            continue

        if padrao_rodape.fullmatch(conteudo):
            continue

        if indice == ultima_linha:
            if coluna is None and (
                padrao_rodape_direita_impar.fullmatch(conteudo)
                or padrao_rodape_esquerda_par.fullmatch(conteudo)
            ):
                continue

            if coluna == "esquerda":
                if pagina_par and padrao_rodape_esquerda_par.fullmatch(
                    conteudo
                ):
                    continue
                if (
                    not pagina_par
                    and linha_anterior_vazia
                    and padrao_rodape_esquerda_impar.fullmatch(conteudo)
                ):
                    continue

            if coluna == "direita":
                if (
                    pagina_par
                    and linha_anterior_vazia
                    and padrao_rodape_direita_par.fullmatch(conteudo)
                ):
                    continue
                if not pagina_par and padrao_rodape_direita_impar.fullmatch(
                    conteudo
                ):
                    continue

        linhas_limpas.append(linha)

    return "\n".join(linhas_limpas).strip()