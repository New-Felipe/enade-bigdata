"""Testes do gerador intermediario ENADE 2017."""
import unittest
from unittest.mock import patch
from extractor.gerar_questoes_2017 import main
MODULO = "extractor.gerar_questoes_2017"
class TestGerarQuestoes2017(unittest.TestCase):
    def executar(self, quantidade=40, falhas=None):
        paginas = [{"texto": "Pagina simulada."}]
        mapeadas = [{"numero_questao": n} for n in range(1, 41)]
        planos = [
            {
                "numero_questao": n,
                "tipo_questao": "objetiva",
                "pagina_inicial": 1,
                "pagina_final_candidata": 1,
            }
            for n in range(1, 41)
        ]
        extraidas = [
            {"numero_questao": n}
            for n in range(1, quantidade + 1)
        ]
        with (
            patch(
                f"{MODULO}.extrair_paginas",
                return_value=paginas,
            ),
            patch(
                f"{MODULO}.mapear_questoes_prova",
                return_value=mapeadas,
            ) as mapear,
            patch(
                f"{MODULO}.planejar_extracao_questoes",
                return_value=planos,
            ),
            patch(
                f"{MODULO}.extrair_questoes_planejadas",
                return_value={
                    "extraidas": extraidas,
                    "falhas": falhas or [],
                    "revisar": [],
                },
            ) as extrair,
            patch(
                f"{MODULO}.salvar_questoes_json",
                return_value=[],
            ) as salvar,
        ):
            try:
                main(
                    executavel_tesseract="tesseract-simulado"
                )
                erro = None
            except RuntimeError as excecao:
                erro = excecao
        return erro, mapear, extrair, salvar
    def test_configura_processamento_2017_com_ocr(self):
        erro, mapear, extrair, salvar = self.executar()
        self.assertIsNone(erro)
        self.assertEqual(
            mapear.call_args.kwargs["executavel_tesseract"],
            "tesseract-simulado",
        )
        parametros = extrair.call_args.kwargs
        self.assertTrue(parametros["priorizar_ocr"])
        self.assertTrue(
            callable(parametros["recuperador_ocr"])
        )
        self.assertEqual(len(parametros["planos"]), 40)
        self.assertEqual(
            parametros["arquivo_origem"],
            "enade_2017_sistemas_de_informacao_prova.pdf",
        )
        salvar.assert_called_once()
        self.assertEqual(
            len(salvar.call_args.args[0]),
            40,
        )
    def test_nao_exporta_extracao_incompleta(self):
        erro, _, _, salvar = self.executar(
            quantidade=39,
            falhas=[{
                "numero_questao": 40,
                "tipo_questao": "objetiva",
                "erro": "Falha simulada.",
            }],
        )
        self.assertIsInstance(erro, RuntimeError)
        salvar.assert_not_called()
if __name__ == "__main__":
    unittest.main()
