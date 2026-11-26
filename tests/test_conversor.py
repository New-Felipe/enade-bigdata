"""Testes da conversao para o modelo canonico ENADE."""

import copy
import json
import unittest

from jsonschema import Draft202012Validator

from extractor.conversor import converter_questao_canonica
from scripts.validar_modelo import CAMINHO_SCHEMA, validar_documento


class TestConversor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        schema = json.loads(
            CAMINHO_SCHEMA.read_text(encoding="utf-8")
        )
        cls.validador = Draft202012Validator(schema)

    def setUp(self):
        self.questao = {
            "numero_questao": 1,
            "tipo_questao": "objetiva",
            "texto": "  Enunciado de teste.  ",
            "alternativas": [
                {"letra": letra, "texto": f"Alternativa {letra}."}
                for letra in "ABCDE"
            ],
            "gabarito": "E",
            "anulada": False,
            "origem": {
                "arquivo": "enade_2021_sistemas_de_informacao_prova.pdf",
                "pagina": 5,
            },
            "pagina_final": 6,
            "validacao_extracao": {
                "status": "extraido_textualmente",
                "quantidade_alternativas": 5,
            },
        }

    def converter_e_validar(self):
        documento = converter_questao_canonica(
            self.questao, 2021
        )

        erros = validar_documento(self.validador, documento)
        self.assertEqual(erros, [])

        return documento

    def test_objetiva_formacao_geral(self):
        documento = self.converter_e_validar()

        self.assertEqual(documento["tipo_conteudo"], "FG")
        self.assertEqual(documento["curso"], "Formação Geral")
        self.assertEqual(
            documento["id"],
            "enade-formacao-geral-2021-fg-obj-q01",
        )
        self.assertEqual(documento["gabarito"], "E")
        self.assertEqual(
            documento["enunciado"], "Enunciado de teste."
        )

    def test_objetiva_componente_especifico_anulada(self):
        self.questao["numero_questao"] = 33
        self.questao["anulada"] = True
        self.questao["gabarito"] = None

        documento = self.converter_e_validar()

        self.assertEqual(documento["tipo_conteudo"], "CE")
        self.assertEqual(
            documento["curso"], "Sistemas de Informação"
        )
        self.assertEqual(documento["gabarito"], None)
        self.assertTrue(documento["anulada"])
        self.assertEqual(len(documento["alternativas"]), 5)

    def test_discursiva_formacao_geral(self):
        self.questao["tipo_questao"] = "discursiva"
        self.questao["numero_questao"] = 2
        self.questao["alternativas"] = []
        self.questao["gabarito"] = None

        documento = self.converter_e_validar()

        self.assertEqual(documento["tipo_conteudo"], "FG")
        self.assertEqual(documento["alternativas"], [])
        self.assertEqual(documento["gabarito"], None)

    def test_discursiva_componente_especifico(self):
        self.questao["tipo_questao"] = "discursiva"
        self.questao["numero_questao"] = 3
        self.questao["alternativas"] = []
        self.questao["gabarito"] = None

        documento = self.converter_e_validar()

        self.assertEqual(documento["tipo_conteudo"], "CE")
        self.assertEqual(
            documento["id"],
            "enade-sistemas-de-informacao-2021-ce-disc-q03",
        )

    def test_preserva_original_e_remove_campos_intermediarios(self):
        original = copy.deepcopy(self.questao)

        documento = self.converter_e_validar()

        self.assertEqual(self.questao, original)
        self.assertNotIn("pagina_final", documento)
        self.assertNotIn("validacao_extracao", documento)
        self.assertEqual(documento["origem"], original["origem"])

    def test_rejeita_questao_sem_gabarito_associado(self):
        del self.questao["gabarito"]

        with self.assertRaises(KeyError):
            converter_questao_canonica(self.questao, 2021)

    def test_preserva_alternativas_graficas_questao_anulada(self):
        """Questao anulada deve preservar referencias aos diagramas."""

        self.questao["numero_questao"] = 33
        self.questao["anulada"] = True
        self.questao["gabarito"] = None

        self.questao["alternativas"] = [
            {
                "letra": letra,
                "imagem": f"imagens/questao_33_{letra}.png",
            }
            for letra in "ABCDE"
        ]

        documento = converter_questao_canonica(
            self.questao, 2021
        )

        self.assertTrue(documento["anulada"])
        self.assertIsNone(documento["gabarito"])
        self.assertEqual(len(documento["alternativas"]), 5)

        for letra, alternativa in zip(
            "ABCDE", documento["alternativas"]
        ):
            self.assertEqual(alternativa["letra"], letra)
            self.assertEqual(
                alternativa["imagem"],
                f"imagens/questao_33_{letra}.png",
            )

        erros = validar_documento(self.validador, documento)
        self.assertEqual(erros, [])

    def test_valida_conteudo_de_alternativas_graficas(self):
        """Aceita imagens validas e rejeita alternativas incompletas."""

        self.questao["numero_questao"] = 33
        self.questao["anulada"] = True
        self.questao["gabarito"] = None

        casos = [
            (
                "somente imagem",
                {"letra": "A", "imagem": "imagens/questao_33_A.png"},
                True,
            ),
            (
                "texto e imagem",
                {
                    "letra": "A",
                    "texto": "Diagrama da tabela hash.",
                    "imagem": "imagens/questao_33_A.png",
                },
                True,
            ),
            (
                "sem texto ou imagem",
                {"letra": "A"},
                False,
            ),
            (
                "imagem vazia",
                {"letra": "A", "imagem": ""},
                False,
            ),
            (
                "imagem somente espacos",
                {"letra": "A", "imagem": "   "},
                False,
            ),
            (
                "texto vazio com imagem valida",
                {
                    "letra": "A",
                    "texto": "",
                    "imagem": "imagens/questao_33_A.png",
                },
                False,
            ),
        ]

        for nome, alternativa, esperado_valido in casos:
            with self.subTest(caso=nome):
                self.questao["alternativas"] = [
                    alternativa,
                    {"letra": "B", "texto": "Outra alternativa."},
                ]

                documento = converter_questao_canonica(
                    self.questao, 2021
                )

                erros = validar_documento(
                    self.validador, documento
                )

                if esperado_valido:
                    self.assertEqual(erros, [])
                else:
                    self.assertTrue(
                        erros,
                        f"O caso {nome!r} deveria ser rejeitado.",
                    )


if __name__ == "__main__":
    unittest.main()
