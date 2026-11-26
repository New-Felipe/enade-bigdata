"""Testes da recuperacao opcional por OCR no planejamento."""
import unittest
from unittest.mock import patch
from extractor.segmenter import extrair_questoes_planejadas
class TestFallbackOCRPlanejado(unittest.TestCase):
    def setUp(self):
        self.paginas = [
            {"texto": ""}
            for _ in range(8)
        ]
        self.plano = {
            "numero_questao": 4,
            "tipo_questao": "objetiva",
            "pagina_inicial": 8,
            "pagina_final_candidata": 8,
        }
        self.questao_recuperada = {
            "numero_questao": 4,
            "tipo_questao": "objetiva",
            "texto": "Enunciado recuperado por OCR.",
            "alternativas": [
                {
                    "letra": letra,
                    "texto": f"Alternativa {letra}",
                }
                for letra in "ABCDE"
            ],
            "origem": {
                "arquivo": "prova.pdf",
                "pagina": 8,
            },
            "pagina_final": 8,
        }
    def executar(self, **opcoes):
        return extrair_questoes_planejadas(
            paginas=self.paginas,
            planos=[self.plano],
            caminho_pdf="prova.pdf",
            arquivo_origem="prova.pdf",
            **opcoes,
        )
    def test_sem_recuperador_preserva_comportamento_atual(self):
        with patch(
            "extractor.segmenter.segmentar_questao_em_paginas",
            side_effect=ValueError("Titulo nao encontrado"),
        ):
            resultado = self.executar()
        self.assertEqual(resultado["extraidas"], [])
        self.assertEqual(len(resultado["falhas"]), 1)
    def test_recupera_quando_segmentacao_falha(self):
        chamadas = []
        def recuperar(plano, caminho_pdf, arquivo_origem):
            chamadas.append(
                (plano, caminho_pdf, arquivo_origem)
            )
            return self.questao_recuperada
        with patch(
            "extractor.segmenter.segmentar_questao_em_paginas",
            side_effect=ValueError("Titulo nao encontrado"),
        ):
            resultado = self.executar(
                recuperador_ocr=recuperar,
            )
        self.assertEqual(resultado["falhas"], [])
        self.assertEqual(
            resultado["extraidas"],
            [self.questao_recuperada],
        )
        self.assertEqual(resultado["revisar"], [])
        self.assertEqual(len(chamadas), 1)
        self.assertEqual(chamadas[0][0], self.plano)
        self.assertEqual(chamadas[0][1], "prova.pdf")
    def test_recupera_objetiva_sem_cinco_alternativas(self):
        incompleta = {
            **self.questao_recuperada,
            "alternativas": [],
        }
        chamadas = []
        def recuperar(plano, caminho_pdf, arquivo_origem):
            chamadas.append(plano)
            return self.questao_recuperada
        with patch(
            "extractor.segmenter.segmentar_questao_em_paginas",
            return_value=incompleta,
        ):
            resultado = self.executar(
                recuperador_ocr=recuperar,
            )
        self.assertEqual(resultado["falhas"], [])
        self.assertEqual(resultado["revisar"], [])
        self.assertEqual(
            resultado["extraidas"],
            [self.questao_recuperada],
        )
        self.assertEqual(len(chamadas), 1)

    def test_rejeita_ocr_de_outra_questao_apos_falha(self):
        incorreta = {
            **self.questao_recuperada,
            "numero_questao": 5,
        }
        with patch(
            "extractor.segmenter.segmentar_questao_em_paginas",
            side_effect=ValueError("Titulo nao encontrado"),
        ):
            resultado = self.executar(
                recuperador_ocr=lambda plano, pdf, origem: incorreta,
            )
        self.assertEqual(resultado["extraidas"], [])
        self.assertEqual(len(resultado["falhas"]), 1)
    def test_nao_substitui_por_ocr_de_outra_questao(self):
        incompleta = {
            **self.questao_recuperada,
            "alternativas": [],
        }
        incorreta = {
            **self.questao_recuperada,
            "numero_questao": 5,
        }
        with patch(
            "extractor.segmenter.segmentar_questao_em_paginas",
            return_value=incompleta,
        ):
            resultado = self.executar(
                recuperador_ocr=lambda plano, pdf, origem: incorreta,
            )
        self.assertEqual(
            resultado["extraidas"],
            [incompleta],
        )
        self.assertEqual(len(resultado["revisar"]), 1)
if __name__ == "__main__":
    unittest.main()
