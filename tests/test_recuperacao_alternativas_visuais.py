"""Testes da recuperacao de alternativas visuais."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_alternativas_visuais import (
    recuperar_alternativas_visuais_duas_colunas,
)
class TestRecuperacaoAlternativasVisuais(unittest.TestCase):
    def setUp(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.base = Path(diretorio.name)
        self.pdf = self.base / "prova.pdf"
        self.saida = self.base / "resultado"
        with pymupdf.open() as documento:
            documento.new_page(width=628, height=827)
            documento.save(self.pdf)
        self.grupo = [
            {
                "letra": letra,
                "x": 65.0 if indice < 3 else 313.7,
                "y": [326.7, 496.8, 666.8, 326.7, 496.8][indice],
            }
            for indice, letra in enumerate("ABCDE")
        ]
    def recuperar(self, grupos, numero_questao=20):
        with patch(
            "extractor.recuperacao_alternativas_visuais."
            "localizar_grupos_alternativas",
            return_value=grupos,
        ):
            return recuperar_alternativas_visuais_duas_colunas(
                self.pdf,
                1,
                numero_questao,
                self.saida,
            )
    def test_gera_cinco_imagens(self):
        alternativas = self.recuperar([self.grupo])
        self.assertEqual(
            [item["letra"] for item in alternativas],
            list("ABCDE"),
        )
        for letra, alternativa in zip("ABCDE", alternativas):
            caminho_esperado = (
                f"imagens/questao_20_{letra}.png"
            )
            self.assertEqual(
                alternativa["imagem"],
                caminho_esperado,
            )
            arquivo = self.saida / caminho_esperado
            self.assertTrue(arquivo.is_file())
            self.assertGreater(arquivo.stat().st_size, 0)
            self.assertTrue(
                arquivo.read_bytes().startswith(
                    b"\x89PNG\r\n\x1a\n"
                )
            )
    def test_rejeita_numero_questao_invalido(self):
        for numero in (0, -1, True, "20"):
            with self.subTest(numero=numero):
                with self.assertRaises(ValueError):
                    self.recuperar(
                        [self.grupo],
                        numero_questao=numero,
                    )
    def test_rejeita_grupo_ausente(self):
        with self.assertRaises(ValueError):
            self.recuperar([])
    def test_rejeita_multiplos_grupos(self):
        with self.assertRaises(ValueError):
            self.recuperar([
                self.grupo,
                self.grupo,
            ])
    def test_rejeita_layout_invalido(self):
        grupo = [
            dict(item) for item in self.grupo
        ]
        grupo[3]["x"] = 80
        with self.assertRaises(ValueError):
            self.recuperar([grupo])
    def test_rejeita_recorte_fora_da_pagina(self):
        grupo = [
            dict(item) for item in self.grupo
        ]
        alturas = [60, 230, 400, 60, 230]
        for item, y in zip(grupo, alturas):
            item["y"] = y
        with self.assertRaises(ValueError):
            self.recuperar([grupo])
        self.assertFalse(
            (self.saida / "imagens").exists()
        )
if __name__ == "__main__":
    unittest.main()
