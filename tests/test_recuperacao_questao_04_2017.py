"""Testes da recuperacao integrada da questao 04 de 2017."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_questao_04_2017 import (
    recuperar_questao_04_2017,
)
class TestRecuperacaoQuestao042017(unittest.TestCase):
    def test_reune_enunciado_alternativas_e_imagem(self):
        with tempfile.TemporaryDirectory() as diretorio:
            base = Path(diretorio)
            pdf = base / "prova.pdf"
            saida = base / "questoes_canonicas"
            with pymupdf.open() as documento:
                for _ in range(8):
                    documento.new_page(
                        width=628,
                        height=827,
                    )
                documento.save(pdf)
            grupos = [[
                {
                    "letra": letra,
                    "x": 60.0,
                    "y": 482.6 + indice * 40,
                }
                for indice, letra in enumerate("ABCDE")
            ]]
            superior = (
                "QUEST\u00c3O 04\n"
                "Sobre a televis\u00e3o, considere a tirinha.\n"
                "TEXTO 1"
            )
            inferior = (
                "Dispon\u00edvel em: fonte original.\n"
                "TEXTO 2\n"
                "Texto de apoio recuperado.\n"
                "Com base nos textos, assinale a alternativa."
            )
            alternativas = [
                {
                    "letra": letra,
                    "texto": f"Alternativa {letra}",
                }
                for letra in "ABCDE"
            ]
            modulo = "extractor.recuperacao_questao_04_2017"
            with (
                patch(
                    f"{modulo}.localizar_grupos_alternativas",
                    return_value=grupos,
                ),
                patch(
                    f"{modulo}.extrair_regiao_ocr",
                    side_effect=[superior, inferior],
                ),
                patch(
                    f"{modulo}.recuperar_alternativas_ocr",
                    return_value=alternativas,
                ),
            ):
                questao = recuperar_questao_04_2017(
                    caminho_pdf=pdf,
                    executavel_tesseract="tesseract-simulado",
                    pasta_saida=saida,
                )
            self.assertEqual(questao["numero_questao"], 4)
            self.assertEqual(questao["tipo_questao"], "objetiva")
            self.assertEqual(questao["origem"]["pagina"], 8)
            self.assertIn(
                "Sobre a televis",
                questao["texto"],
            )
            self.assertIn("TEXTO 2", questao["texto"])
            self.assertNotIn(
                "QUEST\u00c3O 04",
                questao["texto"],
            )
            self.assertEqual(
                [a["letra"] for a in questao["alternativas"]],
                list("ABCDE"),
            )
            referencia = "imagens/questao_04_tirinha.png"
            self.assertEqual(
                questao["imagens_enunciado"],
                [referencia],
            )
            self.assertTrue(
                (saida / referencia).is_file()
            )
if __name__ == "__main__":
    unittest.main()
