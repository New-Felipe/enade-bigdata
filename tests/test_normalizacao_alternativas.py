"""Testes da normalizacao de alternativas do ENADE 2017."""

import unittest

from extractor.normalizacao_alternativas import (
    normalizar_alternativa_romana,
)


class TestNormalizacaoAlternativas(unittest.TestCase):

    def test_alternativas_questao_09(self):
        casos = {
            "A": ("/ \u011e //\u0358", "I e II."),
            "B": ("// \u011e ///\u0358", "II e III."),
            "C": ("/// \u011e /s\u0358", "III e IV."),
            "D": ("/\u0355 // \u011e /s\u0358", "I, II e IV."),
            "E": ("/\u0355 /// \u011e /s\u0358", "I, III e IV."),
        }

        for letra, (original, esperado) in casos.items():
            with self.subTest(letra=letra):
                self.assertEqual(
                    normalizar_alternativa_romana(original),
                    esperado,
                )

    def test_alternativas_questao_10(self):
        casos = {
            "A": ("/ \u011e ///\u0358", "I e III."),
            "B": ("/ \u011e /s\u0358", "I e IV."),
            "C": ("// \u011e /s\u0358", "II e IV."),
            "D": ("/\u0355 // \u011e ///\u0358", "I, II e III."),
            "E": ("//\u0355 /// \u011e /s\u0358", "II, III e IV."),
        }

        for letra, (original, esperado) in casos.items():
            with self.subTest(letra=letra):
                self.assertEqual(
                    normalizar_alternativa_romana(original),
                    esperado,
                )

    def test_rejeita_formatos_desconhecidos(self):
        casos = [
            "texto comum",
            "I e II.",
            "/ e //",
            "",
        ]

        for texto in casos:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    normalizar_alternativa_romana(texto)

    def test_rejeita_entrada_nao_textual(self):
        for valor in (None, 123, [], {}):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    normalizar_alternativa_romana(valor)


if __name__ == "__main__":
    unittest.main()
