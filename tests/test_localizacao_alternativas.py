"""Testes da localizacao automatica de alternativas."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
class TestLocalizacaoAlternativas(unittest.TestCase):
    def setUp(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.pdf = Path(diretorio.name) / "prova.pdf"
        self.pdf.touch()
        self.documento = MagicMock()
        self.documento.__len__.return_value = 1
        self.pagina = MagicMock()
        self.documento.__getitem__.return_value = self.pagina
        patcher = patch(
            "extractor.localizacao_alternativas.pymupdf.open"
        )
        abrir = patcher.start()
        self.addCleanup(patcher.stop)
        abrir.return_value.__enter__.return_value = (
            self.documento
        )
    def configurar_marcadores(self, dados):
        palavras = [
            (x, y, x + 7, y + 10, letra, 0, 0, 0)
            for letra, x, y in dados
        ]
        self.pagina.get_text.return_value = palavras
    def test_localiza_grupo_alinhado(self):
        self.configurar_marcadores([
            (letra, 60.4, 487.6 + indice * 31.6)
            for indice, letra in enumerate("ABCDE")
        ])
        grupos = localizar_grupos_alternativas(
            self.pdf, 1
        )
        self.assertEqual(len(grupos), 1)
        self.assertEqual(
            [item["letra"] for item in grupos[0]],
            list("ABCDE"),
        )
    def test_rejeita_marcadores_desalinhados(self):
        self.configurar_marcadores([
            ("A", 60, 100),
            ("B", 80, 130),
            ("C", 60, 160),
            ("D", 60, 190),
            ("E", 60, 220),
        ])
        grupos = localizar_grupos_alternativas(
            self.pdf, 1
        )
        self.assertEqual(grupos, [])
    def test_rejeita_grupo_incompleto(self):
        self.configurar_marcadores([
            ("A", 60, 100),
            ("B", 60, 130),
            ("C", 60, 160),
            ("D", 60, 190),
        ])
        grupos = localizar_grupos_alternativas(
            self.pdf, 1
        )
        self.assertEqual(grupos, [])
    def test_localiza_grupos_em_duas_colunas(self):
        dados = []
        for x in (60, 320):
            for indice, letra in enumerate("ABCDE"):
                dados.append((
                    letra,
                    x,
                    100 + indice * 25,
                ))
        self.configurar_marcadores(dados)
        grupos = localizar_grupos_alternativas(
            self.pdf, 1
        )
        self.assertEqual(len(grupos), 2)
        self.assertEqual(
            {grupo[0]["x"] for grupo in grupos},
            {60, 320},
        )
    def test_rejeita_pagina_invalida(self):
        for numero in (0, 2, -1, True):
            with self.subTest(numero=numero):
                with self.assertRaises(ValueError):
                    localizar_grupos_alternativas(
                        self.pdf, numero
                    )
    def test_rejeita_pdf_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            localizar_grupos_alternativas(
                self.pdf.parent / "inexistente.pdf",
                1,
            )
if __name__ == "__main__":
    unittest.main()
