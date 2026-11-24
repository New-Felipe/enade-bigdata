"""Testes da associacao de gabaritos oficiais."""

import unittest

from extractor.associacao_gabarito import associar_gabarito


class TestAssociacaoGabarito(unittest.TestCase):

    def setUp(self):
        self.registros = {
            ("objetiva", 1): {
                "gabarito": "E",
                "anulada": False,
            },
            ("objetiva", 33): {
                "gabarito": None,
                "anulada": True,
            },
            ("discursiva", 1): {
                "gabarito": None,
                "anulada": False,
            },
        }

    def test_associa_resposta_objetiva(self):
        questao = {
            "numero_questao": 1,
            "tipo_questao": "objetiva",
            "alternativas": [],
        }

        resultado = associar_gabarito(questao, self.registros)

        self.assertEqual(resultado["gabarito"], "E")
        self.assertFalse(resultado["anulada"])
        self.assertEqual(resultado["numero_questao"], 1)

    def test_associa_questao_anulada(self):
        questao = {
            "numero_questao": 33,
            "tipo_questao": "objetiva",
        }

        resultado = associar_gabarito(questao, self.registros)

        self.assertIsNone(resultado["gabarito"])
        self.assertTrue(resultado["anulada"])

    def test_associa_questao_discursiva(self):
        questao = {
            "numero_questao": 1,
            "tipo_questao": "discursiva",
        }

        resultado = associar_gabarito(questao, self.registros)

        self.assertIsNone(resultado["gabarito"])
        self.assertFalse(resultado["anulada"])

    def test_rejeita_questao_sem_gabarito(self):
        questao = {
            "numero_questao": 99,
            "tipo_questao": "objetiva",
        }

        with self.assertRaisesRegex(
            ValueError,
            "Gabarito nao encontrado",
        ):
            associar_gabarito(questao, self.registros)

    def test_nao_modifica_documento_original(self):
        questao = {
            "numero_questao": 1,
            "tipo_questao": "objetiva",
        }

        resultado = associar_gabarito(questao, self.registros)

        self.assertNotIn("gabarito", questao)
        self.assertNotIn("anulada", questao)
        self.assertIsNot(resultado, questao)


if __name__ == "__main__":
    unittest.main()
