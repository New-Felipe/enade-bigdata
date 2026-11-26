"""Testes da recuperacao de imagens do enunciado."""
import tempfile
import unittest
from pathlib import Path
import pymupdf
from extractor.recuperacao_imagens_enunciado import (
    anexar_imagem_enunciado,
)
class TestRecuperacaoImagensEnunciado(unittest.TestCase):
    def setUp(self):
        diretorio = tempfile.TemporaryDirectory()
        self.addCleanup(diretorio.cleanup)
        self.base = Path(diretorio.name)
        self.pdf = self.base / "prova.pdf"
        self.saida = self.base / "questoes_canonicas"
        with pymupdf.open() as documento:
            documento.new_page(width=628, height=827)
            documento.save(self.pdf)
        self.questao = {
            "numero_questao": 4,
            "tipo_questao": "objetiva",
            "texto": "Sobre a televisao, considere a tirinha.",
            "origem": {
                "arquivo": "prova.pdf",
                "pagina": 1,
            },
        }
    def test_preserva_tirinha_e_referencia(self):
        resultado = anexar_imagem_enunciado(
            questao=self.questao,
            caminho_pdf=self.pdf,
            pasta_saida=self.saida,
            recorte=(55, 148, 573, 318),
            nome_arquivo="questao_04_tirinha.png",
        )
        caminho_relativo = "imagens/questao_04_tirinha.png"
        self.assertEqual(
            resultado["imagens_enunciado"],
            [caminho_relativo],
        )
        self.assertEqual(
            resultado["texto"],
            self.questao["texto"],
        )
        self.assertNotIn(
            "imagens_enunciado",
            self.questao,
        )
        imagem = self.saida / caminho_relativo
        self.assertTrue(imagem.is_file())
        self.assertTrue(
            imagem.read_bytes().startswith(
                b"\x89PNG\r\n\x1a\n"
            )
        )
    def test_rejeita_recorte_fora_da_pagina(self):
        with self.assertRaises(ValueError):
            anexar_imagem_enunciado(
                questao=self.questao,
                caminho_pdf=self.pdf,
                pasta_saida=self.saida,
                recorte=(55, 148, 900, 318),
                nome_arquivo="questao_04_tirinha.png",
            )
        self.assertFalse(
            (self.saida / "imagens").exists()
        )
if __name__ == "__main__":
    unittest.main()
