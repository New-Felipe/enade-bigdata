"""Teste de recuperacao de questao com imagem incorporada."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_questao_imagem import (
    recuperar_questao_com_imagem_incorporada,
)
class TestRecuperacaoQuestaoImagem(unittest.TestCase):
    def test_reune_textos_alternativas_e_imagem_original(self):
        with tempfile.TemporaryDirectory() as diretorio:
            base = Path(diretorio)
            pdf = base / "prova.pdf"
            saida = base / "saida"
            imagem = pymupdf.Pixmap(
                pymupdf.csRGB,
                pymupdf.IRect(0, 0, 10, 8),
                0,
            )
            imagem.clear_with(180)
            with pymupdf.open() as documento:
                pagina = documento.new_page(
                    width=628,
                    height=827,
                )
                pagina.insert_image(
                    pymupdf.Rect(51, 233, 578, 505),
                    stream=imagem.tobytes("png"),
                )
                documento.save(pdf)
            plano = {
                "numero_questao": 5,
                "tipo_questao": "objetiva",
                "pagina_inicial": 1,
                "pagina_final_candidata": 1,
            }
            grupos = [[
                {"letra": letra, "y": 565 + i * 18}
                for i, letra in enumerate("ABCDE")
            ]]
            textos_ocr = [
                (
                    "QUEST\u00c3O 05\n\n"
                    "Hidrog\u00e9is s\u00e3o materiais "
                    "polim\u00e9ricos.\n"
                    "Considere o infogr\u00e1fico abaixo."
                ),
                (
                    "Dispon\u00edvel em: fonte original.\n\n"
                    "Assinale a op\u00e7\u00e3o correta."
                ),
            ]
            alternativas = [
                {
                    "letra": letra,
                    "texto": f"Alternativa {letra}.",
                }
                for letra in "ABCDE"
            ]
            modulo = "extractor.recuperacao_questao_imagem"
            with (
                patch(
                    f"{modulo}.localizar_grupos_alternativas",
                    return_value=grupos,
                ),
                patch(
                    f"{modulo}.extrair_regiao_ocr",
                    side_effect=textos_ocr,
                ) as ocr,
                patch(
                    f"{modulo}.recuperar_alternativas_ocr",
                    return_value=alternativas,
                ),
            ):
                recuperada = recuperar_questao_com_imagem_incorporada(
                    plano=plano,
                    caminho_pdf=pdf,
                    arquivo_origem=pdf.name,
                    executavel_tesseract="tesseract-simulado",
                    pasta_saida=saida,
                    altura_ultima=25,
                )
            self.assertEqual(ocr.call_count, 2)
            self.assertEqual(recuperada["numero_questao"], 5)
            self.assertEqual(recuperada["tipo_questao"], "objetiva")
            self.assertEqual(recuperada["origem"]["pagina"], 1)
            self.assertIn(
                "Considere o infogr\u00e1fico",
                recuperada["texto"],
            )
            self.assertIn(
                "Assinale a op\u00e7\u00e3o correta.",
                recuperada["texto"],
            )
            self.assertNotIn(
                "QUEST\u00c3O 05",
                recuperada["texto"],
            )
            self.assertEqual(
                [a["letra"] for a in recuperada["alternativas"]],
                list("ABCDE"),
            )
            referencia = "imagens/questao_05_infografico.png"
            self.assertEqual(
                recuperada["imagens_enunciado"],
                [referencia],
            )
            caminho_imagem = saida / referencia
            self.assertTrue(caminho_imagem.is_file())
            imagem_salva = pymupdf.Pixmap(str(caminho_imagem))
            self.assertEqual(
                (imagem_salva.width, imagem_salva.height),
                (10, 8),
            )
if __name__ == "__main__":
    unittest.main()
