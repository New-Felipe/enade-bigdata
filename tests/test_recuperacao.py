"""Testes da recuperacao da questao 33 do ENADE 2021."""

import copy
import tempfile
import unittest
from pathlib import Path

import pymupdf

from extractor.recuperacao import recuperar_questao_33


class TestRecuperacaoQuestao33(unittest.TestCase):

    def setUp(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)

        self.base = Path(diretorio.name)
        self.pdf = self.base / "prova.pdf"
        self.imagens = self.base / "imagens"

        documento = pymupdf.open()

        for _ in range(37):
            documento.new_page(width=600, height=800)

        documento.save(self.pdf)
        documento.close()

        self.questao = {
            "numero_questao": 33,
            "tipo_questao": "objetiva",
            "texto": (
                "Enunciado de teste. "
                "insere(17, 9).\n"
                "Conteudo grafico extraido incorretamente."
            ),
            "alternativas": [],
            "origem": {
                "arquivo": "prova.pdf",
                "pagina": 36,
            },
            "pagina_final": 37,
        }

    def test_recupera_cinco_diagramas(self):
        recuperada = recuperar_questao_33(
            self.questao,
            self.pdf,
            self.imagens,
        )

        self.assertEqual(len(recuperada["alternativas"]), 5)

        for letra, alternativa in zip(
            "ABCDE", recuperada["alternativas"]
        ):
            with self.subTest(letra=letra):
                nome = f"questao_33_{letra}.png"
                arquivo = self.imagens / nome

                self.assertEqual(alternativa["letra"], letra)
                self.assertEqual(
                    alternativa["imagem"],
                    f"imagens/{nome}",
                )
                self.assertTrue(arquivo.is_file())
                self.assertGreater(arquivo.stat().st_size, 0)

    def test_preserva_original_e_separa_enunciado(self):
        original = copy.deepcopy(self.questao)

        recuperada = recuperar_questao_33(
            self.questao,
            self.pdf,
            self.imagens,
        )

        self.assertEqual(self.questao, original)
        self.assertEqual(
            recuperada["texto"],
            "Enunciado de teste. insere(17, 9).",
        )

    def test_rejeita_identificacao_incorreta(self):
        casos = [
            {"numero_questao": 32},
            {"tipo_questao": "discursiva"},
            {"pagina_final": 36},
        ]

        for alteracao in casos:
            with self.subTest(alteracao=alteracao):
                questao = copy.deepcopy(self.questao)
                questao.update(alteracao)

                with self.assertRaises(ValueError):
                    recuperar_questao_33(
                        questao,
                        self.pdf,
                        self.imagens,
                    )

    def test_rejeita_fim_do_enunciado_ausente(self):
        self.questao["texto"] = "Enunciado incompleto."

        with self.assertRaises(ValueError):
            recuperar_questao_33(
                self.questao,
                self.pdf,
                self.imagens,
            )

    def test_rejeita_pdf_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            recuperar_questao_33(
                self.questao,
                self.base / "inexistente.pdf",
                self.imagens,
            )

    def test_rejeita_pdf_sem_pagina_37(self):
        pdf_curto = self.base / "prova_curta.pdf"

        documento = pymupdf.open()
        documento.new_page()
        documento.save(pdf_curto)
        documento.close()

        with self.assertRaises(ValueError):
            recuperar_questao_33(
                self.questao,
                pdf_curto,
                self.imagens,
            )


if __name__ == "__main__":
    unittest.main()
