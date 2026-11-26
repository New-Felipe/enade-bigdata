"""Testes de normalizacao de quebras artificiais do OCR."""
import unittest
from extractor.normalizacao_ocr import normalizar_quebras_ocr
class TestNormalizacaoOCR(unittest.TestCase):
    def test_une_quebras_artificiais_de_frases(self):
        entrada = (
            "A televisão se confunde com o anúncio de pasta de\n\n"
            "dentes, que é semelhante à novela. Os programas mal\n\n"
            "se distinguem uns dos outros, com uma sequência "
            "vertiginosa,\n"
            "de imagens.\n\n"
            "Com base nos textos, o veículo\n"
            "de comunicação estimula a"
        )
        esperado = (
            "A televisão se confunde com o anúncio de pasta de "
            "dentes, que é semelhante à novela. Os programas mal "
            "se distinguem uns dos outros, com uma sequência "
            "vertiginosa, de imagens.\n\n"
            "Com base nos textos, o veículo "
            "de comunicação estimula a"
        )
        self.assertEqual(
            normalizar_quebras_ocr(entrada),
            esperado,
        )
    def test_preserva_titulos_e_paragrafos(self):
        entrada = (
            "Sobre a televisão, considere a tirinha.\n\n"
            "TEXTO 1\n\n"
            "Disponível em: <https://exemplo.com>. "
            "Acesso em: 2015.\n\n"
            "TEXTO 2\n\n"
            "A televisão apresenta imagens.\n\n"
            "PEIXOTO, N. B. Referência bibliográfica.\n\n"
            "São Paulo: Editora, 1991."
        )
        self.assertEqual(
            normalizar_quebras_ocr(entrada),
            entrada,
        )
if __name__ == "__main__":
    unittest.main()
