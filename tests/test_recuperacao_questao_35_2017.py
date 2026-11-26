"""Testes da integracao da questao 35 do ENADE 2017."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from extractor.gerar_questoes_2017 import (
    recuperar_questao_2017,
)
MODULO = "extractor.gerar_questoes_2017"
class TestRecuperacaoQuestao352017(unittest.TestCase):
    def executar(self, plano):
        resultado_simulado = {
            "numero_questao": plano["numero_questao"],
            "tipo_questao": "objetiva",
            "texto": "Enunciado recuperado.",
            "alternativas": [
                {"letra": letra, "texto": f"Resposta {letra}"}
                for letra in "ABCDE"
            ],
        }
        with patch(
            f"{MODULO}.recuperar_questao_textual_ocr",
            return_value=resultado_simulado,
        ) as recuperar:
            resultado = recuperar_questao_2017(
                plano=plano,
                caminho_pdf="prova.pdf",
                arquivo_origem="prova.pdf",
                executavel_tesseract="tesseract-simulado",
                pasta_saida="imagens",
            )
        return resultado, recuperar
    def test_questao_35_utiliza_apenas_pagina_35(self):
        plano = {
            "numero_questao": 35,
            "tipo_questao": "objetiva",
            "pagina_inicial": 35,
            "pagina_final_candidata": 39,
            "multiplas_paginas": True,
            "coluna": None,
        }
        original = deepcopy(plano)
        resultado, recuperar = self.executar(plano)
        parametros = recuperar.call_args.kwargs
        plano_ocr = parametros["plano"]
        self.assertEqual(
            resultado["numero_questao"], 35
        )
        self.assertEqual(
            plano_ocr["pagina_inicial"], 35
        )
        self.assertEqual(
            plano_ocr["pagina_final_candidata"], 35
        )
        self.assertFalse(
            plano_ocr["multiplas_paginas"]
        )
        # A ultima alternativa ocupa varias linhas.
        self.assertEqual(
            parametros["altura_ultima"], 60
        )
        # Nao altera o planejamento original.
        self.assertEqual(plano, original)
    def test_outras_questoes_mantem_configuracao(self):
        plano = {
            "numero_questao": 34,
            "tipo_questao": "objetiva",
            "pagina_inicial": 34,
            "pagina_final_candidata": 34,
            "multiplas_paginas": False,
            "coluna": None,
        }
        _, recuperar = self.executar(plano)
        parametros = recuperar.call_args.kwargs
        self.assertEqual(
            parametros["plano"], plano
        )
        self.assertEqual(
            parametros["altura_ultima"], 25
        )
if __name__ == "__main__":
    unittest.main()
