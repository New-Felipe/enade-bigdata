"""Testes da extracao OCR em regioes do PDF."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.ocr import extrair_regiao_ocr
class TestOCRRegiao(unittest.TestCase):
    def setUp(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.pdf = Path(diretorio.name) / "prova.pdf"
        self.tesseract = Path(diretorio.name) / "tesseract.exe"
        documento = pymupdf.open()
        documento.new_page(width=300, height=400)
        documento.save(self.pdf)
        documento.close()
        self.tesseract.touch()
        self.regiao = (20, 30, 200, 110)
    def test_extrai_texto_da_regiao(self):
        simulado = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="contemplação das imagens\n",
            stderr="",
        )
        with patch(
            "extractor.ocr.subprocess.run",
            return_value=simulado,
        ) as executar:
            texto = extrair_regiao_ocr(
                self.pdf,
                1,
                self.regiao,
                self.tesseract,
            )
        self.assertEqual(texto, "contemplação das imagens")
        executar.assert_called_once()
        argumentos = executar.call_args.args[0]
        self.assertIn("--psm", argumentos)
        self.assertEqual(
            argumentos[argumentos.index("--psm") + 1],
            "6",
        )
    def test_rejeita_pagina_invalida(self):
        for numero in (0, 2, -1, True):
            with self.subTest(numero=numero):
                with self.assertRaises(ValueError):
                    extrair_regiao_ocr(
                        self.pdf,
                        numero,
                        self.regiao,
                        self.tesseract,
                    )
    def test_rejeita_regiao_fora_da_pagina(self):
        with self.assertRaises(ValueError):
            extrair_regiao_ocr(
                self.pdf,
                1,
                (-10, 20, 200, 100),
                self.tesseract,
            )
    def test_rejeita_parametros_invalidos(self):
        for dpi in (0, 50, True, "300"):
            with self.subTest(dpi=dpi):
                with self.assertRaises(ValueError):
                    extrair_regiao_ocr(
                        self.pdf,
                        1,
                        self.regiao,
                        self.tesseract,
                        dpi=dpi,
                    )
        for psm in (-1, 14, True, "6"):
            with self.subTest(psm=psm):
                with self.assertRaises(ValueError):
                    extrair_regiao_ocr(
                        self.pdf,
                        1,
                        self.regiao,
                        self.tesseract,
                        psm=psm,
                    )
if __name__ == "__main__":
    unittest.main()
