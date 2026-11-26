"""Testes das objetivas especiais do ENADE 2017."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_objetivas_especiais_2017 import (
    recuperar_questao_04_2017,
)
from copy import deepcopy
from extractor.gerar_questoes_2017 import (
    recuperar_questao_2017,
)
from extractor.revisoes_manuais_2017 import (
    revisar_enunciado_2017,
)
from extractor.revisoes_manuais_2017 import (
    revisar_alternativas_2017,
    revisar_enunciado_2017,
)
from extractor.revisoes_manuais_2017 import (
    revisar_alternativas_2017,
)


class TestRecuperacaoQuestao042017(unittest.TestCase):
    def test_reune_enunciado_alternativas_e_imagem(self):
        with tempfile.TemporaryDirectory() as diretorio:
            base = Path(diretorio)
            pdf = base / "prova.pdf"
            saida = base / "questoes_canonicas"
            with pymupdf.open() as documento:
                for _ in range(8):
                    documento.new_page(
                        width=628,
                        height=827,
                    )
                documento.save(pdf)
            grupos = [[
                {
                    "letra": letra,
                    "x": 60.0,
                    "y": 482.6 + indice * 40,
                }
                for indice, letra in enumerate("ABCDE")
            ]]
            superior = (
                "QUEST\u00c3O 04\n"
                "Sobre a televis\u00e3o, considere a tirinha.\n"
                "TEXTO 1"
            )
            inferior = (
                "Dispon\u00edvel em: fonte original.\n"
                "TEXTO 2\n"
                "Texto de apoio recuperado.\n"
                "Com base nos textos, assinale a alternativa."
            )
            alternativas = [
                {
                    "letra": letra,
                    "texto": f"Alternativa {letra}",
                }
                for letra in "ABCDE"
            ]
            modulo = "extractor.recuperacao_objetivas_especiais_2017"
            with (
                patch(
                    f"{modulo}.localizar_grupos_alternativas",
                    return_value=grupos,
                ),
                patch(
                    f"{modulo}.extrair_regiao_ocr",
                    side_effect=[superior, inferior],
                ),
                patch(
                    f"{modulo}.recuperar_alternativas_ocr",
                    return_value=alternativas,
                ),
            ):
                questao = recuperar_questao_04_2017(
                    caminho_pdf=pdf,
                    executavel_tesseract="tesseract-simulado",
                    pasta_saida=saida,
                )
            self.assertEqual(questao["numero_questao"], 4)
            self.assertEqual(questao["tipo_questao"], "objetiva")
            self.assertEqual(questao["origem"]["pagina"], 8)
            self.assertIn(
                "Sobre a televis",
                questao["texto"],
            )
            self.assertIn("TEXTO 2", questao["texto"])
            self.assertNotIn(
                "QUEST\u00c3O 04",
                questao["texto"],
            )
            self.assertEqual(
                [a["letra"] for a in questao["alternativas"]],
                list("ABCDE"),
            )
            referencia = "imagens/questao_04_tirinha.png"
            self.assertEqual(
                questao["imagens_enunciado"],
                [referencia],
            )
            self.assertTrue(
                (saida / referencia).is_file()
            )


MODULO = "extractor.gerar_questoes_2017"


class TestRecuperacaoQuestao352017(unittest.TestCase):
    def executar(self, plano):
        resultado_simulado = {
            "numero_questao": plano["numero_questao"],
            "tipo_questao": "objetiva",
            "texto": "Enunciado recuperado.",
            "alternativas": [
                {"letra": letra, "texto": f"Resposta {letra}"}
                for letra in "ABCDE"
            ],
        }
        with patch(
            f"{MODULO}.recuperar_questao_textual_ocr",
            return_value=resultado_simulado,
        ) as recuperar:
            resultado = recuperar_questao_2017(
                plano=plano,
                caminho_pdf="prova.pdf",
                arquivo_origem="prova.pdf",
                executavel_tesseract="tesseract-simulado",
                pasta_saida="imagens",
            )
        return resultado, recuperar
    def test_questao_35_utiliza_apenas_pagina_35(self):
        plano = {
            "numero_questao": 35,
            "tipo_questao": "objetiva",
            "pagina_inicial": 35,
            "pagina_final_candidata": 39,
            "multiplas_paginas": True,
            "coluna": None,
        }
        original = deepcopy(plano)
        resultado, recuperar = self.executar(plano)
        parametros = recuperar.call_args.kwargs
        plano_ocr = parametros["plano"]
        self.assertEqual(
            resultado["numero_questao"], 35
        )
        self.assertEqual(
            plano_ocr["pagina_inicial"], 35
        )
        self.assertEqual(
            plano_ocr["pagina_final_candidata"], 35
        )
        self.assertFalse(
            plano_ocr["multiplas_paginas"]
        )
        # A ultima alternativa ocupa varias linhas.
        self.assertEqual(
            parametros["altura_ultima"], 60
        )
        # Nao altera o planejamento original.
        self.assertEqual(plano, original)
    def test_outras_questoes_mantem_configuracao(self):
        plano = {
            "numero_questao": 34,
            "tipo_questao": "objetiva",
            "pagina_inicial": 34,
            "pagina_final_candidata": 34,
            "multiplas_paginas": False,
            "coluna": None,
        }
        _, recuperar = self.executar(plano)
        parametros = recuperar.call_args.kwargs
        self.assertEqual(
            parametros["plano"], plano
        )
        self.assertEqual(
            parametros["altura_ultima"], 25
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


class TestRevisoesManuais2017(unittest.TestCase):
    def setUp(self):
        self.questao = {
            "numero_questao": 14,
            "tipo_questao": "objetiva",
            "texto": "Enunciado da questao 14.",
            "origem": {
                "arquivo": (
                    "enade_2017_sistemas_de_informacao_prova.pdf"
                ),
                "pagina": 21,
            },
            "alternativas": [
                {"letra": letra, "texto": "OCR incorreto"}
                for letra in "ABCDE"
            ],
        }
    def test_corrige_alternativas_verificadas_da_questao_14(self):
        revisada = revisar_alternativas_2017(self.questao)
        esperadas = [
            "I, apenas.",
            "I e III, apenas.",
            "II e IV, apenas.",
            "II, III e IV, apenas.",
            "I, II, III e IV.",
        ]
        self.assertEqual(
            [a["texto"] for a in revisada["alternativas"]],
            esperadas,
        )
        self.assertEqual(
            [a["letra"] for a in revisada["alternativas"]],
            list("ABCDE"),
        )
        self.assertEqual(
            revisada["revisao_manual"]["pagina"],
            21,
        )
        # O resultado original do OCR deve ser preservado.
        self.assertEqual(
            self.questao["alternativas"][0]["texto"],
            "OCR incorreto",
        )
    def test_nao_altera_questoes_sem_revisao(self):
        outra = {
            **self.questao,
            "numero_questao": 15,
            "origem": {
                **self.questao["origem"],
                "pagina": 22,
            },
        }
        revisada = revisar_alternativas_2017(outra)
        self.assertEqual(revisada, outra)
        self.assertIsNot(revisada, outra)
    def test_rejeita_origem_incorreta_da_questao_14(self):
        incorreta = {
            **self.questao,
            "origem": {
                **self.questao["origem"],
                "pagina": 22,
            },
        }
        with self.assertRaises(ValueError):
            revisar_alternativas_2017(incorreta)


class TestRecuperacaoQuestao212017(unittest.TestCase):
    def test_recupera_enunciado_diagrama_e_alternativas(self):
        from extractor.recuperacao_objetivas_especiais_2017 import (
            recuperar_questao_21_2017,
        )

        plano = {
            "numero_questao": 21,
            "tipo_questao": "objetiva",
            "pagina_inicial": 26,
            "pagina_final_candidata": 27,
        }

        questao = recuperar_questao_21_2017(
            plano=plano,
            caminho_pdf="data/raw/enade/2017/sistemas_de_informacao/enade_2017_sistemas_de_informacao_prova.pdf",
            arquivo_origem="enade_2017_sistemas_de_informacao_prova.pdf",
            executavel_tesseract=r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            pasta_saida="data/processed/enade/2017/sistemas_de_informacao/questoes",
        )

        self.assertEqual(questao["numero_questao"], 21)
        self.assertEqual(questao["tipo_questao"], "objetiva")
        self.assertEqual(questao["origem"]["pagina"], 26)
        self.assertEqual(questao["pagina_final"], 27)

        self.assertIn("Uma startup de tecnologia", questao["texto"])
        self.assertIn("Com base no diagrama apresentado", questao["texto"])

        self.assertIn("imagens/questao_21_diagrama_uml.png", questao["imagens_enunciado"])

        self.assertEqual(
            [a["letra"] for a in questao["alternativas"]],
            list("ABCDE"),
        )

        esperadas = [
            "I e II.",
            "I e IV.",
            "II e III.",
            "I, III e IV.",
            "II, III e IV.",
        ]
        self.assertEqual(
            [a["texto"] for a in questao["alternativas"]],
            esperadas,
        )


if __name__ == "__main__":
    unittest.main()

class TestDestinoImagens2017(unittest.TestCase):
    def test_nao_duplica_diretorio_imagens(self):
        from tempfile import TemporaryDirectory
        from extractor.recuperacao_imagens_enunciado import (
            anexar_imagem_enunciado,
            anexar_imagem_incorporada_enunciado,
        )
        with TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            pdf = raiz / "prova.pdf"
            documento = pymupdf.open()
            pagina = documento.new_page(width=200, height=200)
            imagem = pymupdf.Pixmap(
                pymupdf.csRGB,
                pymupdf.IRect(0, 0, 10, 10),
                False,
            )
            imagem.clear_with(200)
            pagina.insert_image(
                pymupdf.Rect(30, 30, 120, 120),
                stream=imagem.tobytes("png"),
            )
            documento.save(str(pdf))
            documento.close()
            questao = {"origem": {"pagina": 1}}
            for modo in ("pasta_base", "pasta_imagens"):
                with self.subTest(modo=modo):
                    base = raiz / modo
                    pasta_saida = (
                        base
                        if modo == "pasta_base"
                        else base / "imagens"
                    )
                    recorte = anexar_imagem_enunciado(
                        questao=questao,
                        caminho_pdf=pdf,
                        pasta_saida=pasta_saida,
                        recorte=(20, 20, 150, 150),
                        nome_arquivo="recorte.png",
                    )
                    incorporada = anexar_imagem_incorporada_enunciado(
                        questao=questao,
                        caminho_pdf=pdf,
                        pasta_saida=pasta_saida,
                        nome_arquivo="incorporada.png",
                    )
                    self.assertTrue(
                        (base / "imagens" / "recorte.png").is_file()
                    )
                    self.assertTrue(
                        (base / "imagens" / "incorporada.png").is_file()
                    )
                    self.assertFalse(
                        (base / "imagens" / "imagens").exists()
                    )
                    self.assertEqual(
                        recorte["imagens_enunciado"],
                        ["imagens/recorte.png"],
                    )
                    self.assertEqual(
                        incorporada["imagens_enunciado"],
                        ["imagens/incorporada.png"],
                    )
