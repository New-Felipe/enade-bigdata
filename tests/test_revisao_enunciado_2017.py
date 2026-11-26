"""Testes da revisao do enunciado da questao 14."""
import unittest
from extractor.revisoes_manuais_2017 import (
    revisar_enunciado_2017,
)
class TestRevisaoEnunciado2017(unittest.TestCase):
    def setUp(self):
        self.questao = {
            "numero_questao": 14,
            "tipo_questao": "objetiva",
            "texto": (
                "Em relacao ao cenario, avalie as afirmacoes.\n\n"
                "|. Primeira afirmacao.\n\n"
                "Il. Segunda afirmacao.\n\n"
                "Ill. Terceira afirmacao.\n\n"
                "IV. Quarta afirmacao.\n\n"
                "O simbolo | no meio da frase deve continuar igual."
            ),
            "origem": {
                "arquivo": (
                    "enade_2017_sistemas_de_informacao_prova.pdf"
                ),
                "pagina": 21,
            },
        }
    def test_corrige_somente_marcadores_das_afirmacoes(self):
        revisada = revisar_enunciado_2017(self.questao)
        for marcador in ("I.", "II.", "III.", "IV."):
            self.assertIn(
                "\n\n" + marcador + " ",
                revisada["texto"],
            )
        self.assertIn(
            "O simbolo | no meio da frase",
            revisada["texto"],
        )
        self.assertEqual(
            revisada["revisao_manual"]["texto_ocr"],
            self.questao["texto"],
        )
        self.assertTrue(
            self.questao["texto"].startswith(
                "Em relacao ao cenario"
            )
        )
    def test_nao_altera_outra_questao(self):
        outra = {
            **self.questao,
            "numero_questao": 15,
        }
        revisada = revisar_enunciado_2017(outra)
        self.assertEqual(revisada, outra)
        self.assertIsNot(revisada, outra)
    def test_rejeita_origem_incorreta(self):
        incorreta = {
            **self.questao,
            "origem": {
                **self.questao["origem"],
                "pagina": 22,
            },
        }
        with self.assertRaises(ValueError):
            revisar_enunciado_2017(incorreta)

    def test_remove_z_isolado_sem_alterar_texto_legitimo(self):
        original = self.questao["texto"]
        texto_ocr = original.replace(
            "\n\n|. Primeira afirmacao.",
            "\n\nZ\n\n|. Primeira afirmacao.",
            1,
        )
        self.assertNotEqual(texto_ocr, original)
        texto_ocr += (
            "\n\nA letra Z nesta frase deve permanecer."
        )
        questao = {
            **self.questao,
            "texto": texto_ocr,
        }
        revisada = revisar_enunciado_2017(questao)
        self.assertNotIn(
            "\n\nZ\n\n",
            revisada["texto"],
        )
        self.assertIn(
            "A letra Z nesta frase deve permanecer.",
            revisada["texto"],
        )
        self.assertIn(
            "\n\nI. Primeira afirmacao.",
            revisada["texto"],
        )
        self.assertEqual(
            revisada["revisao_manual"]["texto_ocr"],
            texto_ocr,
        )
        self.assertEqual(
            questao["texto"],
            texto_ocr,
        )
if __name__ == "__main__":
    unittest.main()
