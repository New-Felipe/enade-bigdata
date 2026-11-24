"""Testes do modulo de OCR."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from extractor.ocr import extrair_coluna_ocr


class TestOCR(unittest.TestCase):

    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.diretorio.cleanup)

        self.pdf = Path(self.diretorio.name) / "teste.pdf"
        self.tesseract = Path(self.diretorio.name) / "tesseract.exe"

        self.tesseract.touch()

    def test_rejeita_pdf_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            extrair_coluna_ocr(
                self.pdf,
                1,
                "direita",
                self.tesseract,
            )

    def test_rejeita_tesseract_inexistente(self):
        self.pdf.touch()
        self.tesseract.unlink()

        with self.assertRaises(FileNotFoundError):
            extrair_coluna_ocr(
                self.pdf,
                1,
                "direita",
                self.tesseract,
            )

    def test_rejeita_coluna_invalida(self):
        self.pdf.touch()

        with self.assertRaises(ValueError):
            extrair_coluna_ocr(
                self.pdf,
                1,
                "centro",
                self.tesseract,
            )

    def test_rejeita_dpi_invalido(self):
        self.pdf.touch()

        for dpi in (0, 50, -1, "250"):
            with self.subTest(dpi=dpi):
                with self.assertRaises(ValueError):
                    extrair_coluna_ocr(
                        self.pdf,
                        1,
                        "direita",
                        self.tesseract,
                        dpi=dpi,
                    )

    def test_extrai_texto_da_coluna(self):
        import pymupdf

        documento = pymupdf.open()
        documento.new_page()
        documento.save(self.pdf)
        documento.close()

        resultado_simulado = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="QUESTAO 10\nTexto do enunciado\n",
            stderr="",
        )

        with patch(
            "extractor.ocr.subprocess.run",
            return_value=resultado_simulado,
        ) as executar:
            texto = extrair_coluna_ocr(
                self.pdf,
                1,
                "direita",
                self.tesseract,
            )

        self.assertEqual(
            texto,
            "QUESTAO 10\nTexto do enunciado",
        )
        executar.assert_called_once()

    def test_rejeita_numero_pagina_invalido(self):
        import pymupdf

        documento = pymupdf.open()
        documento.new_page()
        documento.save(self.pdf)
        documento.close()

        for numero in (0, 2):
            with self.subTest(numero=numero):
                with self.assertRaises(ValueError):
                    extrair_coluna_ocr(
                        self.pdf,
                        numero,
                        "direita",
                        self.tesseract,
                    )


if __name__ == "__main__":
    unittest.main()
