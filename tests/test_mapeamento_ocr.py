"""Testes da integracao OCR ao mapeamento de questoes."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.segmenter import mapear_questoes_prova
class TestMapeamentoOCR(unittest.TestCase):
    def setUp(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.pdf = Path(diretorio.name) / "prova.pdf"
        with pymupdf.open() as documento:
            documento.new_page(width=600, height=800)
            documento.save(self.pdf)
        self.paginas = [{
            "pagina": 1,
            "texto": (
                "Yh ^d K 15\n"
                "QUEST\u00c3O 16\n"
            ),
        }]
    def test_comportamento_original_sem_ocr(self):
        resultado = mapear_questoes_prova(
            self.paginas,
            str(self.pdf),
        )
        self.assertEqual(resultado, [{
            "numero_questao": 16,
            "tipo_questao": "objetiva",
            "pagina": 1,
            "coluna": None,
        }])
    def test_recupera_titulo_corrompido_em_duas_colunas(self):
        with patch(
            "extractor.ocr.extrair_regiao_ocr",
            side_effect=[
                "QUEST\u00c3O 15 \u2014\u2014",
                "QUEST\u00c3O 16 \u2014\u2014",
            ],
        ):
            resultado = mapear_questoes_prova(
                self.paginas,
                str(self.pdf),
                executavel_tesseract="tesseract-simulado",
            )
        self.assertEqual(resultado, [
            {
                "numero_questao": 15,
                "tipo_questao": "objetiva",
                "pagina": 1,
                "coluna": "esquerda",
            },
            {
                "numero_questao": 16,
                "tipo_questao": "objetiva",
                "pagina": 1,
                "coluna": "direita",
            },
        ])
if __name__ == "__main__":
    unittest.main()
