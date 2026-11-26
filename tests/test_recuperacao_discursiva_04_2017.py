"""Testes da recuperacao da discursiva 04 do ENADE 2017."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_discursiva_04_2017 import (
    recuperar_discursiva_04_2017,
)
MODULO = "extractor.recuperacao_discursiva_04_2017"
class TestRecuperacaoDiscursiva042017(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        base = Path(self.temporario.name)
        self.pdf = base / "prova.pdf"
        self.imagens = base / "questoes" / "imagens"
        with pymupdf.open() as documento:
            for _ in range(14):
                documento.new_page(width=628, height=827)
            pagina = documento[13]
            pagina.draw_rect(
                pymupdf.Rect(200, 160, 430, 300)
            )
            documento.save(self.pdf)
        self.plano = {
            "numero_questao": 4,
            "tipo_questao": "discursiva",
            "pagina_inicial": 14,
            "pagina_final_candidata": 14,
        }
        self.texto_ocr = (
            "Exame Nacional de Desempenho\n"
            "QUEST\u00c3O DISCURSIVA 04\n\n"
            "A figura a seguir representa uma "
            "planta\u00e7\u00e3o de caf\u00e9 com x colunas "
            "e y linhas.\n\n"
            "Considerando uma solu\u00e7\u00e3o algor\u00edtmica "
            "para contar as falhas, fa\u00e7a o que se pede.\n\n"
            "a) Indique o tipo de estrutura de dados "
            "utilizada na solu\u00e7\u00e3o.\n"
            "b) Escreva o algoritmo da solu\u00e7\u00e3o "
            "em pseudoc\u00f3digo.\n\n"
            "RASCUNHO\n"
            "1\n2\n3\n"
            "\u00c1rea livre"
        )
    def recuperar(self, texto):
        with patch(
            f"{MODULO}.extrair_regiao_ocr",
            return_value=texto,
        ):
            return recuperar_discursiva_04_2017(
                plano=self.plano,
                caminho_pdf=self.pdf,
                arquivo_origem=self.pdf.name,
                executavel_tesseract="tesseract-simulado",
                pasta_saida=self.imagens,
            )
    def test_recupera_texto_e_preserva_figura(self):
        questao = self.recuperar(self.texto_ocr)
        self.assertEqual(questao["numero_questao"], 4)
        self.assertEqual(
            questao["tipo_questao"],
            "discursiva",
        )
        self.assertEqual(questao["origem"]["pagina"], 14)
        self.assertEqual(questao["pagina_final"], 14)
        self.assertEqual(questao["alternativas"], [])
        texto = questao["texto"]
        self.assertIn("planta\u00e7\u00e3o de caf\u00e9", texto)
        self.assertIn("a) Indique", texto)
        self.assertIn("b) Escreva", texto)
        # Os itens discursivos devem permanecer separados.
        self.assertIn("\nb) Escreva", texto)
        self.assertNotIn("RASCUNHO", texto)
        self.assertNotIn("\u00c1rea livre", texto)
        self.assertEqual(
            questao["imagens_enunciado"],
            ["imagens/discursiva_04_cafezal.png"],
        )
        imagem = self.imagens / "discursiva_04_cafezal.png"
        self.assertTrue(imagem.is_file())
        self.assertGreater(imagem.stat().st_size, 500)
    def test_rejeita_titulo_de_outra_questao(self):
        texto_incorreto = self.texto_ocr.replace(
            "QUEST\u00c3O DISCURSIVA 04",
            "QUEST\u00c3O DISCURSIVA 05",
        )
        with self.assertRaises(ValueError):
            self.recuperar(texto_incorreto)
if __name__ == "__main__":
    unittest.main()
