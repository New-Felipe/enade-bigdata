"""Testes de recuperacao OCR de questoes textuais."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_questao_textual_ocr import (
    recuperar_questao_textual_ocr,
)
class TestRecuperacaoQuestaoTextualOCR(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pdf = Path(self.temporario.name) / "prova.pdf"
        with pymupdf.open() as documento:
            documento.new_page(width=628, height=827)
            documento.save(self.pdf)
        self.plano = {
            "numero_questao": 14,
            "tipo_questao": "objetiva",
            "pagina_inicial": 1,
            "pagina_final_candidata": 1,
        }
        self.grupos = [[
            {"letra": letra, "y": 490 + indice * 20}
            for indice, letra in enumerate("ABCDE")
        ]]
        self.alternativas = [
            {"letra": letra, "texto": f"Resposta {letra}."}
            for letra in "ABCDE"
        ]
    def recuperar(self, texto_ocr):
        modulo = "extractor.recuperacao_questao_textual_ocr"
        with (
            patch(
                f"{modulo}.localizar_grupos_alternativas",
                return_value=self.grupos,
            ),
            patch(
                f"{modulo}.extrair_regiao_ocr",
                return_value=texto_ocr,
            ),
            patch(
                f"{modulo}.recuperar_alternativas_ocr",
                return_value=self.alternativas,
            ),
        ):
            return recuperar_questao_textual_ocr(
                plano=self.plano,
                caminho_pdf=self.pdf,
                arquivo_origem=self.pdf.name,
                executavel_tesseract="tesseract-simulado",
                altura_ultima=25,
            )
    def test_recupera_questao_textual(self):
        texto = (
            "QUEST\u00c3O 14\n\n"
            "Considere o sistema de informa\u00e7\u00e3o.\n\n"
            "I. Primeira afirma\u00e7\u00e3o.\n"
            "II. Segunda afirma\u00e7\u00e3o.\n\n"
            "Assinale a alternativa correta."
        )
        questao = self.recuperar(texto)
        self.assertEqual(questao["numero_questao"], 14)
        self.assertEqual(questao["tipo_questao"], "objetiva")
        self.assertEqual(questao["origem"]["pagina"], 1)
        self.assertIn(
            "Considere o sistema",
            questao["texto"],
        )
        self.assertNotIn(
            "QUEST\u00c3O 14",
            questao["texto"],
        )
        self.assertEqual(
            [a["letra"] for a in questao["alternativas"]],
            list("ABCDE"),
        )
        self.assertNotIn("imagens_enunciado", questao)
    def test_rejeita_titulo_de_outra_questao(self):
        texto = (
            "QUEST\u00c3O 15\n\n"
            "Enunciado de outra quest\u00e3o."
        )
        with self.assertRaises(ValueError):
            self.recuperar(texto)

    def verificar_recuperacao_por_coluna(self, coluna, numero):
        self.plano["coluna"] = coluna
        self.plano["numero_questao"] = numero
        grupos = [
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
        texto_ocr = (
            f"QUEST\u00c3O {numero}\n\n"
            f"Enunciado da questao {numero}.\n\n"
            "Assinale a alternativa correta."
        )
        modulo = "extractor.recuperacao_questao_textual_ocr"
        with (
            patch(
                f"{modulo}.localizar_grupos_alternativas",
                return_value=grupos,
            ),
            patch(
                f"{modulo}.extrair_regiao_ocr",
                return_value=texto_ocr,
            ) as ocr,
            patch(
                f"{modulo}.recuperar_alternativas_ocr",
                return_value=self.alternativas,
            ) as recuperar_alternativas,
        ):
            questao = recuperar_questao_textual_ocr(
                plano=self.plano,
                caminho_pdf=self.pdf,
                arquivo_origem=self.pdf.name,
                executavel_tesseract="tesseract-simulado",
            )
        regiao = ocr.call_args.kwargs["regiao"]
        centro = 628 / 2
        if coluna == "esquerda":
            self.assertLess(regiao[0], centro)
            self.assertLessEqual(regiao[2], centro)
        else:
            self.assertGreaterEqual(regiao[0], centro)
            self.assertGreater(regiao[2], centro)
        self.assertIn(
            f"Enunciado da questao {numero}",
            questao["texto"],
        )
        self.assertEqual(
            recuperar_alternativas.call_args.kwargs["coluna"],
            coluna,
        )
        self.assertEqual(
            [a["letra"] for a in questao["alternativas"]],
            list("ABCDE"),
        )
    def test_recupera_enunciado_coluna_esquerda(self):
        self.verificar_recuperacao_por_coluna(
            coluna="esquerda",
            numero=15,
        )
    def test_recupera_enunciado_coluna_direita(self):
        self.verificar_recuperacao_por_coluna(
            coluna="direita",
            numero=16,
        )
if __name__ == "__main__":
    unittest.main()
