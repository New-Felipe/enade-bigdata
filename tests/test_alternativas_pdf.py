"""Testes da recuperacao de alternativas diretamente do PDF."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from extractor.alternativas_pdf import (
    extrair_grupos_alternativas_romanas,
)


class TestAlternativasPDF(unittest.TestCase):

    def setUp(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)

        self.pdf = Path(diretorio.name) / "prova.pdf"
        self.pdf.touch()

        self.documento = MagicMock()
        self.documento.__len__.return_value = 1

        self.pagina = MagicMock()
        self.pagina.rect.width = 628

        self.documento.__getitem__.return_value = self.pagina

        patcher = patch("extractor.alternativas_pdf.pymupdf.open")
        abrir = patcher.start()
        self.addCleanup(patcher.stop)

        abrir.return_value.__enter__.return_value = self.documento

    def configurar_palavras(self, dados):
        palavras = []

        for x, y_inicial, alternativas in dados:
            for indice, (letra, texto) in enumerate(
                zip("ABCDE", alternativas)
            ):
                y = y_inicial + indice * 17.2

                palavras.append(
                    (x, y, x + 7, y + 10, letra, 0, 0, 0)
                )

                for posicao, palavra in enumerate(texto.split()):
                    px = x + 15 + posicao * 25

                    palavras.append(
                        (px, y, px + 20, y + 10,
                         palavra, 0, 0, posicao)
                    )

        self.pagina.get_text.return_value = palavras

    def test_recupera_duas_colunas(self):
        esquerda = [
            "/ \u011e //\u0358",
            "// \u011e ///\u0358",
            "/// \u011e /s\u0358",
            "/\u0355 // \u011e /s\u0358",
            "/\u0355 /// \u011e /s\u0358",
        ]

        direita = [
            "/ \u011e ///\u0358",
            "/ \u011e /s\u0358",
            "// \u011e /s\u0358",
            "/\u0355 // \u011e ///\u0358",
            "//\u0355 /// \u011e /s\u0358",
        ]

        self.configurar_palavras([
            (60, 590, esquerda),
            (320, 430, direita),
        ])

        grupos = extrair_grupos_alternativas_romanas(
            self.pdf, 1
        )

        self.assertEqual(len(grupos), 2)
        self.assertEqual(
            [grupo["coluna"] for grupo in grupos],
            ["esquerda", "direita"],
        )

        self.assertEqual(
            [a["texto"] for a in grupos[0]["alternativas"]],
            [
                "I e II.",
                "II e III.",
                "III e IV.",
                "I, II e IV.",
                "I, III e IV.",
            ],
        )

        self.assertEqual(
            [a["texto"] for a in grupos[1]["alternativas"]],
            [
                "I e III.",
                "I e IV.",
                "II e IV.",
                "I, II e III.",
                "II, III e IV.",
            ],
        )

    def test_rejeita_pagina_invalida(self):
        for numero in (0, 2, -1, True):
            with self.subTest(numero=numero):
                with self.assertRaises(ValueError):
                    extrair_grupos_alternativas_romanas(
                        self.pdf, numero
                    )

    def test_rejeita_pdf_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            extrair_grupos_alternativas_romanas(
                self.pdf.parent / "inexistente.pdf", 1
            )

    def test_sem_grupos_retorna_lista_vazia(self):
        self.pagina.get_text.return_value = []

        resultado = extrair_grupos_alternativas_romanas(
            self.pdf, 1
        )

        self.assertEqual(resultado, [])

    def test_rejeita_alternativa_desconhecida(self):
        self.configurar_palavras([
            (60, 400, ["???"] * 5),
        ])

        with self.assertRaises(ValueError):
            extrair_grupos_alternativas_romanas(
                self.pdf, 1
            )


if __name__ == "__main__":
    unittest.main()
