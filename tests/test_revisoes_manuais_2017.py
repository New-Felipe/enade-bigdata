"""Testes das revisoes manuais verificadas do ENADE 2017."""
import unittest
from extractor.revisoes_manuais_2017 import (
    revisar_alternativas_2017,
)
class TestRevisoesManuais2017(unittest.TestCase):
    def setUp(self):
        self.questao = {
            "numero_questao": 14,
            "tipo_questao": "objetiva",
            "texto": "Enunciado da questao 14.",
            "origem": {
                "arquivo": (
                    "enade_2017_sistemas_de_informacao_prova.pdf"
                ),
                "pagina": 21,
            },
            "alternativas": [
                {"letra": letra, "texto": "OCR incorreto"}
                for letra in "ABCDE"
            ],
        }
    def test_corrige_alternativas_verificadas_da_questao_14(self):
        revisada = revisar_alternativas_2017(self.questao)
        esperadas = [
            "I, apenas.",
            "I e III, apenas.",
            "II e IV, apenas.",
            "II, III e IV, apenas.",
            "I, II, III e IV.",
        ]
        self.assertEqual(
            [a["texto"] for a in revisada["alternativas"]],
            esperadas,
        )
        self.assertEqual(
            [a["letra"] for a in revisada["alternativas"]],
            list("ABCDE"),
        )
        self.assertEqual(
            revisada["revisao_manual"]["pagina"],
            21,
        )
        # O resultado original do OCR deve ser preservado.
        self.assertEqual(
            self.questao["alternativas"][0]["texto"],
            "OCR incorreto",
        )
    def test_nao_altera_questoes_sem_revisao(self):
        outra = {
            **self.questao,
            "numero_questao": 15,
            "origem": {
                **self.questao["origem"],
                "pagina": 22,
            },
        }
        revisada = revisar_alternativas_2017(outra)
        self.assertEqual(revisada, outra)
        self.assertIsNot(revisada, outra)
    def test_rejeita_origem_incorreta_da_questao_14(self):
        incorreta = {
            **self.questao,
            "origem": {
                **self.questao["origem"],
                "pagina": 22,
            },
        }
        with self.assertRaises(ValueError):
            revisar_alternativas_2017(incorreta)
if __name__ == "__main__":
    unittest.main()
