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
    def test_recupera_alternativas_visuais_da_questao_20(self):
        extraidas = [
            {
                "numero_questao": numero,
                "tipo_questao": "objetiva",
                "origem": {
                    "pagina": 25 if numero == 20 else 1
                },
                "alternativas": [],
            }
            for numero in range(1, 41)
        ]
        alternativas_visuais = [
            {
                "letra": letra,
                "imagem": f"imagens/questao_20_{letra}.png",
            }
            for letra in "ABCDE"
        ]
        revisoes = [
            {
                "tipo_questao": "objetiva",
                "numero_questao": numero,
                "motivo": "Alternativas A-E nao identificadas",
            }
            for numero in (20, 21)
        ]
        with (
            patch(
                f"{MODULO}.extrair_paginas",
                return_value=[{"texto": "Pagina simulada."}],
            ),
            patch(
                f"{MODULO}.mapear_questoes_prova",
                return_value=[{}] * 40,
            ),
            patch(
                f"{MODULO}.planejar_extracao_questoes",
                return_value=[],
            ),
            patch(
                f"{MODULO}.extrair_questoes_planejadas",
                return_value={
                    "extraidas": extraidas,
                    "falhas": [],
                    "revisar": revisoes,
                },
            ),
            patch(
                f"{MODULO}.recuperar_alternativas_visuais_duas_colunas",
                return_value=alternativas_visuais,
            ) as recuperar,
            patch(
                f"{MODULO}.salvar_questoes_json",
            ) as salvar,
        ):
            with self.assertRaises(RuntimeError) as contexto:
                main(executavel_tesseract="tesseract-simulado")
        questao_20 = extraidas[19]
        self.assertEqual(
            questao_20["alternativas"],
            alternativas_visuais,
        )
        self.assertEqual(
            [a["letra"] for a in questao_20["alternativas"]],
            list("ABCDE"),
        )
        recuperar.assert_called_once()
        parametros = recuperar.call_args.kwargs
        self.assertEqual(parametros["numero_pagina"], 25)
        self.assertEqual(parametros["numero_questao"], 20)
        mensagem = str(contexto.exception)
        self.assertIn("1 pendencias de revisao", mensagem)
        self.assertIn("objetiva 21:", mensagem)
        self.assertNotIn("objetiva 20:", mensagem)
        salvar.assert_not_called()
    def test_objetiva_21_ajusta_apenas_copia_do_plano(self):
        from extractor.gerar_questoes_2017 import (
            recuperar_questao_2017,
        )
        plano = {
            "numero_questao": 21,
            "tipo_questao": "objetiva",
            "pagina_inicial": 26,
            "pagina_final_candidata": 26,
            "multiplas_paginas": False,
        }
        with patch(
            f"{MODULO}.recuperar_questao_21_2017",
            return_value={"numero_questao": 21},
        ) as recuperar:
            resultado = recuperar_questao_2017(
                plano=plano,
                caminho_pdf="prova.pdf",
                arquivo_origem="prova.pdf",
                executavel_tesseract="tesseract-simulado",
                pasta_saida="imagens",
            )
        recuperar.assert_called_once()
        plano_enviado = recuperar.call_args.kwargs["plano"]
        self.assertEqual(
            plano_enviado["pagina_inicial"], 26
        )
        self.assertEqual(
            plano_enviado["pagina_final_candidata"], 27
        )
        self.assertTrue(plano_enviado["multiplas_paginas"])
        # O planejamento original permanece intacto.
        self.assertEqual(plano["pagina_final_candidata"], 26)
        self.assertFalse(plano["multiplas_paginas"])
        self.assertIsNot(plano_enviado, plano)
        self.assertEqual(resultado["numero_questao"], 21)
    def test_geracao_canonica_2017_simula_sem_gravar(self):
        import io
        from contextlib import redirect_stdout
        from pathlib import Path
        from unittest.mock import patch
        import extractor.gerar_canonicos_2017 as canonicos
        if (
            not canonicos.GABARITO_PDF.is_file()
            or len(list(canonicos.ENTRADA.glob("*.json"))) != 40
        ):
            self.skipTest("Acervo ENADE 2017 indisponivel.")
        saida = io.StringIO()
        with (
            patch.object(
                Path,
                "write_text",
                side_effect=AssertionError("Gravacao inesperada"),
            ) as gravar,
            patch.object(
                Path,
                "mkdir",
                side_effect=AssertionError("Criacao inesperada"),
            ) as criar,
            patch.object(
                canonicos.shutil,
                "copy2",
                side_effect=AssertionError("Copia inesperada"),
            ) as copiar,
            redirect_stdout(saida),
        ):
            canonicos.main(gravar=False)
        self.assertIn(
            "Canonicos validados: 40",
            saida.getvalue(),
        )
        self.assertIn(
            "Imagens verificadas: 10",
            saida.getvalue(),
        )
        self.assertIn(
            "Modo: SIMULACAO",
            saida.getvalue(),
        )
        gravar.assert_not_called()
        criar.assert_not_called()
        copiar.assert_not_called()
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
