"""Testes da recuperacao OCR de alternativas por coluna."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_alternativas_ocr import (
    recuperar_alternativas_ocr,
)
MODULO = "extractor.recuperacao_alternativas_ocr"
class TestAlternativasOCRColunas(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pdf = Path(self.temporario.name) / "prova.pdf"
        with pymupdf.open() as documento:
            documento.new_page(width=628, height=827)
            documento.save(self.pdf)
        # Mesma ordem encontrada na pagina 22 real.
        self.grupos = [
            [
                {
                    "letra": letra,
                    "x": 320.04,
                    "y": 473.15 + indice * 17.23,
                }
                for indice, letra in enumerate("ABCDE")
            ],
            [
                {
                    "letra": letra,
                    "x": 60.33,
                    "y": 624.36 + indice * 29.64,
                }
                for indice, letra in enumerate("ABCDE")
            ],
        ]
    def verificar_coluna(self, coluna, x_esperado):
        with (
            patch(
                f"{MODULO}.localizar_grupos_alternativas",
                return_value=self.grupos,
            ),
            patch(
                f"{MODULO}.extrair_regiao_ocr",
                return_value="Resposta simulada",
            ) as ocr,
        ):
            alternativas = recuperar_alternativas_ocr(
                caminho_pdf=self.pdf,
                numero_pagina=1,
                executavel_tesseract="tesseract-simulado",
                deslocamento_texto=18,
                margem_direita=35,
                altura_ultima=25,
                coluna=coluna,
            )
        self.assertEqual(
            [a["letra"] for a in alternativas],
            list("ABCDE"),
        )
        self.assertEqual(ocr.call_count, 5)
        centro = 628 / 2
        for chamada in ocr.call_args_list:
            regiao = chamada.kwargs["regiao"]
            self.assertAlmostEqual(
                regiao[0],
                x_esperado + 18,
                delta=1,
            )
            self.assertLess(regiao[0], regiao[2])
            if coluna == "esquerda":
                self.assertLessEqual(
                    regiao[2],
                    centro,
                )
            else:
                self.assertGreaterEqual(
                    regiao[0],
                    centro,
                )
    def test_seleciona_grupo_da_coluna_esquerda(self):
        self.verificar_coluna(
            coluna="esquerda",
            x_esperado=60.33,
        )
    def test_seleciona_grupo_da_coluna_direita(self):
        self.verificar_coluna(
            coluna="direita",
            x_esperado=320.04,
        )
if __name__ == "__main__":
    unittest.main()
