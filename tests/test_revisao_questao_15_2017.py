"""Testes das revisoes verificadas da questao 15/2017."""
import unittest
from extractor.revisoes_manuais_2017 import (
    revisar_alternativas_2017,
    revisar_enunciado_2017,
)
class TestRevisaoQuestao152017(unittest.TestCase):
    def setUp(self):
        self.questao = {
            "numero_questao": 15,
            "tipo_questao": "objetiva",
            "texto": (
                "Considerando esse cenario, avalie as "
                "assercoes a seguir.\n\n"
                "| A abordagem ASI estabelece um mapeamento "
                "da organizacao.\n\n"
                "PORQUE\n\n"
                "Il. O objetivo da ASI e inter-relacionar dados.\n\n"
                "A respeito dessas assercoes, assinale "
                "a opcao correta."
            ),
            "alternativas": [
                {
                    "letra": "A",
                    "texto": (
                        "As asser\u00e7\u00f5es le Il s\u00e3o proposi\u00e7\u00f5es "
                        "verdadeiras, e a Il \u00e9 uma justificativa "
                        "correta de 1."
                    ),
                },
                {
                    "letra": "B",
                    "texto": (
                        "As asser\u00e7\u00f5es le Il s\u00e3o proposi\u00e7\u00f5es "
                        "verdadeiras, mas a Il n\u00e3o \u00e9 uma "
                        "justificativa correta de |."
                    ),
                },
                {
                    "letra": "C",
                    "texto": (
                        "A asser\u00e7\u00e3o | \u00e9 uma proposi\u00e7\u00e3o "
                        "verdadeira, e a ll \u00e9 uma proposi\u00e7\u00e3o "
                        "falsa."
                    ),
                },
                {
                    "letra": "D",
                    "texto": (
                        "A asser\u00e7\u00e3o | \u00e9 uma proposi\u00e7\u00e3o "
                        "falsa, e a Il \u00e9 uma proposi\u00e7\u00e3o "
                        "verdadeira."
                    ),
                },
                {
                    "letra": "E",
                    "texto": (
                        "As asser\u00e7\u00f5es | e Il s\u00e3o "
                        "proposi\u00e7\u00f5es falsas. |"
                    ),
                },
            ],
            "origem": {
                "arquivo": (
                    "enade_2017_sistemas_de_informacao_prova.pdf"
                ),
                "pagina": 22,
            },
        }
    def test_corrige_alternativas_verificadas(self):
        revisada = revisar_alternativas_2017(
            self.questao
        )
        esperadas = [
            (
                "As asser\u00e7\u00f5es I e II s\u00e3o proposi\u00e7\u00f5es "
                "verdadeiras, e a II \u00e9 uma justificativa "
                "correta de I."
            ),
            (
                "As asser\u00e7\u00f5es I e II s\u00e3o proposi\u00e7\u00f5es "
                "verdadeiras, mas a II n\u00e3o \u00e9 uma "
                "justificativa correta de I."
            ),
            (
                "A asser\u00e7\u00e3o I \u00e9 uma proposi\u00e7\u00e3o "
                "verdadeira, e a II \u00e9 uma proposi\u00e7\u00e3o "
                "falsa."
            ),
            (
                "A asser\u00e7\u00e3o I \u00e9 uma proposi\u00e7\u00e3o "
                "falsa, e a II \u00e9 uma proposi\u00e7\u00e3o "
                "verdadeira."
            ),
            (
                "As asser\u00e7\u00f5es I e II s\u00e3o "
                "proposi\u00e7\u00f5es falsas."
            ),
        ]
        self.assertEqual(
            [a["texto"] for a in revisada["alternativas"]],
            esperadas,
        )
        self.assertEqual(
            revisada["revisao_manual"]["alternativas_ocr"],
            self.questao["alternativas"],
        )
    def test_corrige_marcadores_do_enunciado(self):
        revisada = revisar_enunciado_2017(
            self.questao
        )
        self.assertIn(
            "I. A abordagem ASI",
            revisada["texto"],
        )
        self.assertIn(
            "II. O objetivo da ASI",
            revisada["texto"],
        )
        self.assertIn(
            "PORQUE",
            revisada["texto"],
        )
        self.assertEqual(
            revisada["revisao_manual"]["texto_ocr"],
            self.questao["texto"],
        )
if __name__ == "__main__":
    unittest.main()
