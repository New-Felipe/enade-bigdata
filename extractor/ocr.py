"""Extracao de texto de colunas de PDFs usando OCR."""

import subprocess
import tempfile
from pathlib import Path

import pymupdf


def extrair_coluna_ocr(
    caminho_pdf,
    numero_pagina,
    coluna,
    executavel_tesseract,
    dpi=250,
):
    """Extrai texto de uma coluna usando Tesseract OCR."""

    caminho = Path(caminho_pdf)
    tesseract = Path(executavel_tesseract)

    if not caminho.is_file():
        raise FileNotFoundError(f"PDF nao encontrado: {caminho}")

    if not tesseract.is_file():
        raise FileNotFoundError(
            f"Tesseract nao encontrado: {tesseract}"
        )

    if coluna not in ("esquerda", "direita"):
        raise ValueError("Coluna invalida.")

    if not isinstance(dpi, int) or dpi < 72:
        raise ValueError("Resolucao DPI invalida.")

    with pymupdf.open(caminho) as documento:
        if not 1 <= numero_pagina <= len(documento):
            raise ValueError("Numero de pagina invalido.")

        pagina = documento[numero_pagina - 1]
        meio = pagina.rect.width / 2

        if coluna == "esquerda":
            area = pymupdf.Rect(
                0, 0, meio, pagina.rect.height
            )
        else:
            area = pymupdf.Rect(
                meio, 0, pagina.rect.width, pagina.rect.height
            )

        imagem = pagina.get_pixmap(dpi=dpi, clip=area)

        with tempfile.TemporaryDirectory() as diretorio:
            caminho_imagem = Path(diretorio) / "coluna.png"
            imagem.save(caminho_imagem)

            resultado = subprocess.run(
                [
                    str(tesseract),
                    str(caminho_imagem),
                    "stdout",
                    "-l", "por",
                    "--psm", "4",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )

            return resultado.stdout.strip()
