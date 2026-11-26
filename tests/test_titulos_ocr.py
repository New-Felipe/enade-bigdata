"""Testes do reconhecimento de titulos recuperados por OCR."""
import unittest
from extractor.segmenter import (
    identificar_titulo,
    identificar_titulo_ocr,
)
class TestIdentificarTituloOCR(unittest.TestCase):
    def test_titulos_com_tracos_decorativos(self):
        amostras = {
            15: "QUEST\u00c3O 15 \u2014\u2014\u2014",
            16: "QUEST\u00c3O 16 \u2014\u2014",
            24: "QUEST\u00c3O 24 \u2014\u2014\u2014",
            25: "QUEST\u00c3O 25 \u2014\u2014",
            33: "QUEST\u00c3O33 \u2014\u2014\u2014",
            34: "QUEST\u00c3O 34 \u2014\u2014",
        }
        for numero, texto in amostras.items():
            with self.subTest(numero=numero):
                self.assertEqual(
                    identificar_titulo_ocr(texto),
                    {
                        "numero_questao": numero,
                        "tipo_questao": "objetiva",
                    },
                )
    def test_titulo_convencional(self):
        self.assertEqual(
            identificar_titulo_ocr("QUESTAO 20"),
            {
                "numero_questao": 20,
                "tipo_questao": "objetiva",
            },
        )
    def test_titulo_discursivo(self):
        self.assertEqual(
            identificar_titulo_ocr("QUESTAO DISCURSIVA 03"),
            {
                "numero_questao": 3,
                "tipo_questao": "discursiva",
            },
        )
    def test_rejeita_texto_adicional(self):
        self.assertIsNone(
            identificar_titulo_ocr(
                "QUESTAO 15 resposta incorreta"
            )
        )
    def test_rejeita_linha_sem_titulo(self):
        self.assertIsNone(
            identificar_titulo_ocr(
                "Os sistemas de informacao ampliaram"
            )
        )
    def test_identificacao_original_permanece_estrita(self):
        self.assertIsNone(
            identificar_titulo(
                "QUEST\u00c3O 15 \u2014\u2014"
            )
        )

    def test_titulos_discursivos_com_variacoes_ocr(self):
        amostras = {
            4: "QUEST\u00c3O DISCURSIVA04 \u2014\u2014\u2014\u2014",
            5: "QUEST\u00c3O DISCURSIVA 05 \u2014=>>>>>>>>>>>>>>\u2014\u2014",
        }
        for numero, titulo in amostras.items():
            with self.subTest(numero=numero):
                self.assertEqual(
                    identificar_titulo_ocr(titulo),
                    {
                        "numero_questao": numero,
                        "tipo_questao": "discursiva",
                    },
                )

if __name__ == "__main__":
    unittest.main()
