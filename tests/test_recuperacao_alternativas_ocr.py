"""Testes da recuperacao integrada de alternativas por OCR."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_alternativas_ocr import (
    recuperar_alternativas_ocr,
)
class TestRecuperacaoAlternativasOCR(unittest.TestCase):
    def setUp(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.pdf = Path(diretorio.name) / "prova.pdf"
        self.tesseract = Path(diretorio.name) / "tesseract.exe"
        documento = pymupdf.open()
        documento.new_page(width=628, height=827)
        documento.save(self.pdf)
        documento.close()
        self.tesseract.touch()
        self.grupo = [
            {
                "letra": letra,
                "x": 60,
                "y": 487 + indice * 31,
            }
            for indice, letra in enumerate("ABCDE")
        ]
        self.parametros = {
            "deslocamento_texto": 18,
            "margem_direita": 35,
            "altura_ultima": 40,
        }
    def test_recupera_cinco_alternativas(self):
        textos = [
            "Texto da alternativa A",
            "Texto da alternativa B",
            "Texto da alternativa C",
            "Texto da alternativa D",
            "Texto da alternativa E",
        ]
        with (
            patch(
                "extractor.recuperacao_alternativas_ocr."
                "localizar_grupos_alternativas",
                return_value=[self.grupo],
            ),
            patch(
                "extractor.recuperacao_alternativas_ocr."
                "extrair_regiao_ocr",
                side_effect=textos,
            ) as extrair,
        ):
            alternativas = recuperar_alternativas_ocr(
                self.pdf,
                1,
                self.tesseract,
                **self.parametros,
            )
        self.assertEqual(len(alternativas), 5)
        self.assertEqual(
            [a["letra"] for a in alternativas],
            list("ABCDE"),
        )
        self.assertEqual(
            [a["texto"] for a in alternativas],
            textos,
        )
        self.assertEqual(extrair.call_count, 5)
    def test_normaliza_quebras_de_linha(self):
        with (
            patch(
                "extractor.recuperacao_alternativas_ocr."
                "localizar_grupos_alternativas",
                return_value=[self.grupo],
            ),
            patch(
                "extractor.recuperacao_alternativas_ocr."
                "extrair_regiao_ocr",
                return_value="Texto em\n duas linhas ",
            ),
        ):
            alternativas = recuperar_alternativas_ocr(
                self.pdf,
                1,
                self.tesseract,
                **self.parametros,
            )
        self.assertEqual(
            alternativas[0]["texto"],
            "Texto em duas linhas",
        )
    def test_rejeita_grupo_ausente(self):
        with patch(
            "extractor.recuperacao_alternativas_ocr."
            "localizar_grupos_alternativas",
            return_value=[],
        ):
            with self.assertRaises(ValueError):
                recuperar_alternativas_ocr(
                    self.pdf,
                    1,
                    self.tesseract,
                    **self.parametros,
                )
    def test_rejeita_multiplos_grupos(self):
        with patch(
            "extractor.recuperacao_alternativas_ocr."
            "localizar_grupos_alternativas",
            return_value=[self.grupo, self.grupo],
        ):
            with self.assertRaises(ValueError):
                recuperar_alternativas_ocr(
                    self.pdf,
                    1,
                    self.tesseract,
                    **self.parametros,
                )
    def test_rejeita_texto_vazio(self):
        with (
            patch(
                "extractor.recuperacao_alternativas_ocr."
                "localizar_grupos_alternativas",
                return_value=[self.grupo],
            ),
            patch(
                "extractor.recuperacao_alternativas_ocr."
                "extrair_regiao_ocr",
                return_value="  ",
            ),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Texto ausente na alternativa A",
            ):
                recuperar_alternativas_ocr(
                    self.pdf,
                    1,
                    self.tesseract,
                    **self.parametros,
                )
if __name__ == "__main__":
    unittest.main()
