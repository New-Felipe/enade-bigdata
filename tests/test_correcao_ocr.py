"""Testes das correcoes controladas de OCR."""

import unittest

from extractor.correcao_ocr import corrigir_numeracao_afirmacoes


class TestCorrecaoOCR(unittest.TestCase):

    def setUp(self):
        self.numeracao = ["I", "II", "III", "IV"]

    def test_corrige_questao_09(self):
        original = (
            "Il. Regra de negocio: entregar o sorvete\n"
            "Il. Regra de negocio: aplicar promocoes\n"
            "ll. Regra de negocio: aceitar pagamentos\n"
            "IV. Regra de negocio: conceder desconto"
        )

        esperado = (
            "I. Regra de negocio: entregar o sorvete\n"
            "II. Regra de negocio: aplicar promocoes\n"
            "III. Regra de negocio: aceitar pagamentos\n"
            "IV. Regra de negocio: conceder desconto"
        )

        resultado = corrigir_numeracao_afirmacoes(
            original, self.numeracao
        )

        self.assertEqual(resultado, esperado)

    def test_corrige_questao_10(self):
        original = (
            "Il. Osriscos em um projeto\n"
            "Il. O impacto do risco\n"
            "Il. Devem ser desconsiderados os riscos\n"
            "IV. O valor estimado"
        )

        esperado = (
            "I. Osriscos em um projeto\n"
            "II. O impacto do risco\n"
            "III. Devem ser desconsiderados os riscos\n"
            "IV. O valor estimado"
        )

        resultado = corrigir_numeracao_afirmacoes(
            original, self.numeracao
        )

        self.assertEqual(resultado, esperado)

    def test_preserva_texto_e_espacamento(self):
        original = (
            "Introducao da questao.\n"
            "\n"
            "  Il. Primeira afirmacao.\n"
            "II. Segunda afirmacao.\n"
            "lll. Terceira afirmacao.\n"
            "IV. Quarta afirmacao.\n"
            "\n"
            "Conclusao do enunciado."
        )

        resultado = corrigir_numeracao_afirmacoes(
            original, self.numeracao
        )

        esperado = original.replace(
            "  Il.", "  I."
        ).replace(
            "lll.", "III."
        )

        self.assertEqual(resultado, esperado)
        self.assertIn("\n\n", resultado)

    def test_rejeita_entradas_invalidas(self):
        texto_valido = (
            "I. Primeira\n"
            "II. Segunda\n"
            "III. Terceira\n"
            "IV. Quarta"
        )

        casos = [
            ("", self.numeracao),
            (None, self.numeracao),
            ("I. Apenas uma afirmacao", self.numeracao),
            (texto_valido, ["I", "II", "III"]),
            (texto_valido, None),
            (texto_valido, "I II III IV"),
        ]

        for texto, numeracao in casos:
            with self.subTest(
                texto=texto,
                numeracao=numeracao,
            ):
                with self.assertRaises(ValueError):
                    corrigir_numeracao_afirmacoes(
                        texto, numeracao
                    )


if __name__ == "__main__":
    unittest.main()
