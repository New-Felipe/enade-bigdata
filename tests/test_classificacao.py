"""Testes da classificacao FG/CE das questoes ENADE."""

import unittest

from extractor.classificacao import classificar_tipo_conteudo


class TestClassificacao(unittest.TestCase):

    def test_objetivas_formacao_geral(self):
        for numero in (1, 8):
            with self.subTest(numero=numero):
                questao = {
                    "tipo_questao": "objetiva",
                    "numero_questao": numero,
                }

                resultado = classificar_tipo_conteudo(
                    questao, 2021
                )

                self.assertEqual(resultado, "FG")

    def test_objetivas_componente_especifico(self):
        for numero in (9, 35):
            with self.subTest(numero=numero):
                questao = {
                    "tipo_questao": "objetiva",
                    "numero_questao": numero,
                }

                resultado = classificar_tipo_conteudo(
                    questao, 2021
                )

                self.assertEqual(resultado, "CE")

    def test_discursivas_formacao_geral(self):
        for numero in (1, 2):
            with self.subTest(numero=numero):
                questao = {
                    "tipo_questao": "discursiva",
                    "numero_questao": numero,
                }

                resultado = classificar_tipo_conteudo(
                    questao, 2021
                )

                self.assertEqual(resultado, "FG")

    def test_discursivas_componente_especifico(self):
        for numero in (3, 5):
            with self.subTest(numero=numero):
                questao = {
                    "tipo_questao": "discursiva",
                    "numero_questao": numero,
                }

                resultado = classificar_tipo_conteudo(
                    questao, 2021
                )

                self.assertEqual(resultado, "CE")

    def test_rejeita_ano_nao_configurado(self):
        questao = {
            "tipo_questao": "objetiva",
            "numero_questao": 1,
        }

        with self.assertRaisesRegex(
            ValueError,
            "Classificacao nao configurada",
        ):
            classificar_tipo_conteudo(questao, 2023)

    def test_rejeita_questoes_invalidas(self):
        casos = [
            ("objetiva", 0),
            ("objetiva", 36),
            ("discursiva", 6),
            ("desconhecida", 1),
            ("objetiva", True),
        ]

        for tipo, numero in casos:
            with self.subTest(tipo=tipo, numero=numero):
                questao = {
                    "tipo_questao": tipo,
                    "numero_questao": numero,
                }

                with self.assertRaises(ValueError):
                    classificar_tipo_conteudo(
                        questao, 2021
                    )


if __name__ == "__main__":
    unittest.main()
