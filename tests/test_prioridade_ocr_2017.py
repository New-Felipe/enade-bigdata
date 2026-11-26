"""Testes da prioridade opcional de recuperacao OCR."""
import unittest
from unittest.mock import patch
from extractor.segmenter import extrair_questoes_planejadas
class TestPrioridadeOCR2017(unittest.TestCase):
    def setUp(self):
        self.plano = {
            "numero_questao": 14,
            "tipo_questao": "objetiva",
            "pagina_inicial": 1,
            "pagina_final_candidata": 1,
        }
        alternativas = [
            {"letra": letra, "texto": f"Alternativa {letra}"}
            for letra in "ABCDE"
        ]
        self.convencional = {
            "numero_questao": 14,
            "tipo_questao": "objetiva",
            "texto": "Texto convencional com problemas.",
            "alternativas": alternativas,
        }
        self.recuperada = {
            "numero_questao": 14,
            "tipo_questao": "objetiva",
            "texto": "Texto OCR revisado.",
            "alternativas": alternativas,
        }
    def executar(self, recuperador, **opcoes):
        with patch(
            "extractor.segmenter.segmentar_questao_em_paginas",
            return_value=self.convencional,
        ):
            return extrair_questoes_planejadas(
                paginas=[{"texto": ""}],
                planos=[self.plano],
                caminho_pdf="prova.pdf",
                arquivo_origem="prova.pdf",
                recuperador_ocr=recuperador,
                **opcoes,
            )
    def test_prioriza_ocr_mesmo_com_cinco_alternativas(self):
        chamadas = []
        def recuperar(plano, pdf, origem):
            chamadas.append(plano["numero_questao"])
            return self.recuperada
        resultado = self.executar(
            recuperar,
            priorizar_ocr=True,
        )
        self.assertEqual(chamadas, [14])
        self.assertEqual(resultado["falhas"], [])
        self.assertEqual(resultado["revisar"], [])
        self.assertEqual(
            resultado["extraidas"][0]["texto"],
            "Texto OCR revisado.",
        )
    def test_mantem_comportamento_padrao_do_2021(self):
        chamadas = []
        def recuperar(plano, pdf, origem):
            chamadas.append(plano["numero_questao"])
            return self.recuperada
        resultado = self.executar(recuperar)
        self.assertEqual(chamadas, [])
        self.assertEqual(resultado["falhas"], [])
        self.assertEqual(
            resultado["extraidas"][0]["texto"],
            "Texto convencional com problemas.",
        )

    def test_falha_do_ocr_utiliza_extracao_convencional(self):
        chamadas = []
        def recuperar(plano, pdf, origem):
            chamadas.append(plano["numero_questao"])
            raise ValueError("Falha simulada no OCR.")
        resultado = self.executar(
            recuperar,
            priorizar_ocr=True,
        )
        self.assertEqual(chamadas, [14])
        self.assertEqual(resultado["falhas"], [])
        self.assertEqual(resultado["revisar"], [])
        self.assertEqual(
            resultado["extraidas"][0]["texto"],
            "Texto convencional com problemas.",
        )
    def test_ocr_invalido_utiliza_extracao_convencional(self):
        chamadas = []
        alternativas = [
            dict(alternativa)
            for alternativa in self.recuperada["alternativas"]
        ]
        alternativas[0].pop("letra")
        def recuperar(plano, pdf, origem):
            chamadas.append(plano["numero_questao"])
            return {
                **self.recuperada,
                "alternativas": alternativas,
            }
        resultado = self.executar(
            recuperar,
            priorizar_ocr=True,
        )
        self.assertEqual(chamadas, [14])
        self.assertEqual(resultado["falhas"], [])
        self.assertEqual(resultado["revisar"], [])
        self.assertEqual(
            resultado["extraidas"][0]["texto"],
            "Texto convencional com problemas.",
        )
if __name__ == "__main__":
    unittest.main()
