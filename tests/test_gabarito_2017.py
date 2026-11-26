"""Testes do gabarito tabular do ENADE 2017."""
import unittest
from extractor.gabarito import interpretar_gabarito
class TestGabarito2017(unittest.TestCase):
    def test_interpreta_tabela_com_anulacao(self):
        texto = """
GABARITO DEFINITIVO DAS QUESTÕES DE MÚLTIPLA ESCOLHA
Sistemas de Informação
ITEM      GABARITO
   1          C
   2          C
   3          B
   4          B
  14       ANULADA
  35          C
"""
        registros = interpretar_gabarito(texto)
        self.assertEqual(len(registros), 6)
        self.assertEqual(
            registros[("objetiva", 4)],
            {"gabarito": "B", "anulada": False},
        )
        self.assertEqual(
            registros[("objetiva", 14)],
            {"gabarito": None, "anulada": True},
        )
        self.assertEqual(
            registros[("objetiva", 35)],
            {"gabarito": "C", "anulada": False},
        )
    def test_rejeita_itens_duplicados(self):
        texto = """
ITEM GABARITO
1 C
1 B
"""
        with self.assertRaisesRegex(
            ValueError,
            "duplicada",
        ):
            interpretar_gabarito(texto)
if __name__ == "__main__":
    unittest.main()
