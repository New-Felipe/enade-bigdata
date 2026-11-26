"""Testes de recuperacao de imagens incorporadas em PDFs."""
import tempfile
import unittest
from pathlib import Path
import pymupdf
from extractor.recuperacao_imagens_enunciado import (
    anexar_imagem_incorporada_enunciado,
)
class TestImagensIncorporadas(unittest.TestCase):
    def test_extrai_imagem_original_e_preserva_questao(self):
        with tempfile.TemporaryDirectory() as diretorio:
            base = Path(diretorio)
            pdf = base / "prova.pdf"
            saida = base / "questoes_canonicas"
            imagem_teste = pymupdf.Pixmap(
                pymupdf.csRGB,
                pymupdf.IRect(0, 0, 10, 8),
                0,
            )
            imagem_teste.clear_with(180)
            with pymupdf.open() as documento:
                pagina = documento.new_page(
                    width=300,
                    height=400,
                )
                pagina.insert_image(
                    pymupdf.Rect(40, 80, 240, 240),
                    stream=imagem_teste.tobytes("png"),
                )
                documento.save(pdf)
            questao = {
                "numero_questao": 5,
                "tipo_questao": "objetiva",
                "texto": "Considere o infografico.",
                "origem": {
                    "arquivo": pdf.name,
                    "pagina": 1,
                },
            }
            recuperada = anexar_imagem_incorporada_enunciado(
                questao=questao,
                caminho_pdf=pdf,
                pasta_saida=saida,
                nome_arquivo="questao_05_infografico.png",
            )
            referencia = "imagens/questao_05_infografico.png"
            self.assertEqual(
                recuperada["imagens_enunciado"],
                [referencia],
            )
            self.assertNotIn("imagens_enunciado", questao)
            caminho_imagem = saida / referencia
            self.assertTrue(caminho_imagem.is_file())
            imagem = pymupdf.Pixmap(str(caminho_imagem))
            self.assertEqual(imagem.width, 10)
            self.assertEqual(imagem.height, 8)
    def test_rejeita_pagina_sem_imagem(self):
        with tempfile.TemporaryDirectory() as diretorio:
            base = Path(diretorio)
            pdf = base / "prova.pdf"
            with pymupdf.open() as documento:
                documento.new_page()
                documento.save(pdf)
            questao = {
                "numero_questao": 5,
                "tipo_questao": "objetiva",
                "texto": "Enunciado.",
                "origem": {
                    "arquivo": pdf.name,
                    "pagina": 1,
                },
            }
            with self.assertRaises(ValueError):
                anexar_imagem_incorporada_enunciado(
                    questao=questao,
                    caminho_pdf=pdf,
                    pasta_saida=base / "saida",
                    nome_arquivo="infografico.png",
                )
if __name__ == "__main__":
    unittest.main()
