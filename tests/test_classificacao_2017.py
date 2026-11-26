"""Testes da classificacao das questoes ENADE 2017."""
import unittest
from extractor.classificacao import classificar_tipo_conteudo
class TestClassificacao2017(unittest.TestCase):
    def test_objetivas_formacao_geral(self):
        for numero in (1, 4, 8):
            with self.subTest(numero=numero):
                questao = {
                    "tipo_questao": "objetiva",
                    "numero_questao": numero,
                }
                self.assertEqual(
                    classificar_tipo_conteudo(questao, 2017),
                    "FG",
                )
    def test_objetivas_componente_especifico(self):
        for numero in (9, 20, 35):
            with self.subTest(numero=numero):
                questao = {
                    "tipo_questao": "objetiva",
                    "numero_questao": numero,
                }
                self.assertEqual(
                    classificar_tipo_conteudo(questao, 2017),
                    "CE",
                )
    def test_discursivas(self):
        casos = {
            1: "FG",
            2: "FG",
            3: "CE",
            4: "CE",
            5: "CE",
        }
        for numero, esperado in casos.items():
            with self.subTest(numero=numero):
                questao = {
                    "tipo_questao": "discursiva",
                    "numero_questao": numero,
                }
                self.assertEqual(
                    classificar_tipo_conteudo(questao, 2017),
                    esperado,
                )
    def test_ano_2021_continua_suportado(self):
        questao = {
            "tipo_questao": "objetiva",
            "numero_questao": 4,
        }
        self.assertEqual(
            classificar_tipo_conteudo(questao, 2021),
            "FG",
        )

    def test_rejeita_anos_nao_configurados(self):
        questao = {
            "tipo_questao": "objetiva",
            "numero_questao": 4,
        }
        for ano in (2016, 2022, 2023):
            with self.subTest(ano=ano):
                with self.assertRaises(ValueError):
                    classificar_tipo_conteudo(questao, ano)
    def test_rejeita_numeros_fora_dos_intervalos(self):
        casos = [
            ("objetiva", 0),
            ("objetiva", 36),
            ("discursiva", 0),
            ("discursiva", 6),
        ]
        for tipo, numero in casos:
            with self.subTest(tipo=tipo, numero=numero):
                questao = {
                    "tipo_questao": tipo,
                    "numero_questao": numero,
                }
                with self.assertRaises(ValueError):
                    classificar_tipo_conteudo(questao, 2017)

if __name__ == "__main__":
    unittest.main()
