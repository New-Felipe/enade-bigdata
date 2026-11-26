"""Testes automatizados da interpretação de gabaritos ENADE."""

import unittest

from extractor.gabarito import interpretar_gabarito


class TestInterpretarGabarito(unittest.TestCase):

    def test_questoes_objetivas(self):
        texto = """
        QUESTÃO 1 E
        QUESTÃO 2 C
        QUESTÃO 3 B
        """

        resultado = interpretar_gabarito(texto)

        self.assertEqual(len(resultado), 3)
        self.assertEqual(
            resultado[("objetiva", 1)],
            {"gabarito": "E", "anulada": False},
        )
        self.assertEqual(
            resultado[("objetiva", 2)]["gabarito"],
            "C",
        )

    def test_questao_anulada(self):
        resultado = interpretar_gabarito(
            "QUESTÃO 33 ANULADA"
        )

        self.assertEqual(
            resultado[("objetiva", 33)],
            {"gabarito": None, "anulada": True},
        )

    def test_questao_discursiva(self):
        resultado = interpretar_gabarito(
            "QUESTÃO DISCURSIVA 1 ***"
        )

        self.assertEqual(
            resultado[("discursiva", 1)],
            {"gabarito": None, "anulada": False},
        )

    def test_questoes_duplicadas(self):
        texto = """
        QUESTÃO 1 A
        QUESTÃO 1 B
        """

        with self.assertRaisesRegex(
            ValueError,
            "Questao duplicada",
        ):
            interpretar_gabarito(texto)

    def test_texto_sem_gabarito(self):
        with self.assertRaisesRegex(
            ValueError,
            "Nenhuma questao encontrada",
        ):
            interpretar_gabarito(
                "Documento sem respostas reconhecíveis."
            )


if __name__ == "__main__":
    unittest.main()
