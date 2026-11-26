"""Testes das questoes discursivas do ENADE 2017."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from extractor.recuperacao_discursivas_2017 import (
    recuperar_discursiva_04_2017,
    recuperar_discursiva_05_2017,
)
MODULO = "extractor.recuperacao_discursivas_2017"
class TestRecuperacaoDiscursiva042017(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        base = Path(self.temporario.name)
        self.pdf = base / "prova.pdf"
        self.imagens = base / "questoes" / "imagens"
        with pymupdf.open() as documento:
            for _ in range(14):
                documento.new_page(width=628, height=827)
            pagina = documento[13]
            pagina.draw_rect(
                pymupdf.Rect(200, 160, 430, 300)
            )
            documento.save(self.pdf)
        self.plano = {
            "numero_questao": 4,
            "tipo_questao": "discursiva",
            "pagina_inicial": 14,
            "pagina_final_candidata": 14,
        }
        self.texto_ocr = (
            "Exame Nacional de Desempenho\n"
            "QUEST\u00c3O DISCURSIVA 04\n\n"
            "A figura a seguir representa uma "
            "planta\u00e7\u00e3o de caf\u00e9 com x colunas "
            "e y linhas.\n\n"
            "Considerando uma solu\u00e7\u00e3o algor\u00edtmica "
            "para contar as falhas, fa\u00e7a o que se pede.\n\n"
            "a) Indique o tipo de estrutura de dados "
            "utilizada na solu\u00e7\u00e3o.\n"
            "b) Escreva o algoritmo da solu\u00e7\u00e3o "
            "em pseudoc\u00f3digo.\n\n"
            "RASCUNHO\n"
            "1\n2\n3\n"
            "\u00c1rea livre"
        )
    def recuperar(self, texto):
        with patch(
            f"{MODULO}.extrair_regiao_ocr",
            return_value=texto,
        ):
            return recuperar_discursiva_04_2017(
                plano=self.plano,
                caminho_pdf=self.pdf,
                arquivo_origem=self.pdf.name,
                executavel_tesseract="tesseract-simulado",
                pasta_saida=self.imagens,
            )
    def test_recupera_texto_e_preserva_figura(self):
        questao = self.recuperar(self.texto_ocr)
        self.assertEqual(questao["numero_questao"], 4)
        self.assertEqual(
            questao["tipo_questao"],
            "discursiva",
        )
        self.assertEqual(questao["origem"]["pagina"], 14)
        self.assertEqual(questao["pagina_final"], 14)
        self.assertEqual(questao["alternativas"], [])
        texto = questao["texto"]
        self.assertIn("planta\u00e7\u00e3o de caf\u00e9", texto)
        self.assertIn("a) Indique", texto)
        self.assertIn("b) Escreva", texto)
        # Os itens discursivos devem permanecer separados.
        self.assertIn("\nb) Escreva", texto)
        self.assertNotIn("RASCUNHO", texto)
        self.assertNotIn("\u00c1rea livre", texto)
        self.assertEqual(
            questao["imagens_enunciado"],
            ["imagens/discursiva_04_cafezal.png"],
        )
        imagem = self.imagens / "discursiva_04_cafezal.png"
        self.assertTrue(imagem.is_file())
        self.assertGreater(imagem.stat().st_size, 500)
    def test_rejeita_titulo_de_outra_questao(self):
        texto_incorreto = self.texto_ocr.replace(
            "QUEST\u00c3O DISCURSIVA 04",
            "QUEST\u00c3O DISCURSIVA 05",
        )
        with self.assertRaises(ValueError):
            self.recuperar(texto_incorreto)

class TestRecuperacaoDiscursiva052017(unittest.TestCase):
    def setUp(self):
        self.pdf = Path(
            "data/raw/enade/2017/sistemas_de_informacao/"
            "enade_2017_sistemas_de_informacao_prova.pdf"
        )
        self.saida = Path(
            "data/processed/enade/2017/sistemas_de_informacao/"
            "previews/teste_discursiva_05"
        )
        self.arquivo_origem = self.pdf.name

    def test_recupera_texto_da_discursiva_05(self):
        questao = recuperar_discursiva_05_2017(
            caminho_pdf=self.pdf,
            arquivo_origem=self.arquivo_origem,
            executavel_tesseract=(
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            ),
            pasta_saida=self.saida,
        )

        self.assertEqual(questao["numero_questao"], 5)
        self.assertEqual(questao["tipo_questao"], "discursiva")
        self.assertEqual(questao["origem"]["pagina"], 15)
        self.assertEqual(questao["pagina_final"], 15)
        self.assertEqual(questao["alternativas"], [])

        texto = questao["texto"]

        self.assertIn("Durante as Olimpíadas de 2016", texto)
        self.assertIn("sistema de agendamento de competições de tiro esportivo", texto)
        self.assertIn("Competições masculinas", texto)
        self.assertIn("Competições femininas", texto)
        self.assertIn("Fossa olímpica dupla", texto)
        self.assertIn("comitê olímpico nacional", texto)
        self.assertIn("diagrama de classe da UML", texto)

        self.assertNotIn("RASCUNHO", texto)

        # Verifica a fidelidade dos tres topicos da prova.
        self.assertIn(
            "realiza\u00e7\u00e3o, o hor\u00e1rio de in\u00edcio",
            texto,
        )
        self.assertIn(
            "\n\u2022 o equipamento utilizado,",
            texto,
        )
        self.assertIn(
            "\n\u2022 o tipo de alvo e a dist\u00e2ncia,",
            texto,
        )
        self.assertIn(
            "\n\u2022 a posi\u00e7\u00e3o do atirador",
            texto,
        )
        # Evita confundir a letra O com o algarismo zero.
        self.assertIn("Pistola 50 m", texto)
        self.assertNotIn("Pistola 5O m", texto)

        self.assertNotIn("Área livre", texto)

    def test_preserva_colunas_da_tabela_em_texto(self):
        questao = recuperar_discursiva_05_2017(
            caminho_pdf=self.pdf,
            arquivo_origem=self.arquivo_origem,
            executavel_tesseract=(
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            ),
            pasta_saida=self.saida,
        )
        texto = questao["texto"]
        linhas_esperadas = (
            "| Competi\u00e7\u00f5es masculinas | Competi\u00e7\u00f5es femininas |",
            "| Pistola de ar 10 m | Pistola de ar 10 m |",
            "| Carabina de ar 10 m | Carabina de ar 10 m |",
            "| Pistola r\u00e1pida 25 m | Pistola 25 m |",
            "| Pistola 50 m | Carabina tr\u00eas posi\u00e7\u00f5es 50 m |",
            "| Carabina deitado 50 m | Skeet |",
            "| Carabina tr\u00eas posi\u00e7\u00f5es 50 m | Fossa ol\u00edmpica |",
            "| Skeet | |",
            "| Fossa ol\u00edmpica | |",
            "| Fossa ol\u00edmpica dupla | |",
        )
        faltantes = [
            linha
            for linha in linhas_esperadas
            if linha not in texto
        ]
        self.assertEqual(
            faltantes,
            [],
            "A tabela textual nao preservou suas duas colunas.",
        )
    def test_rejeita_titulo_de_outra_questao(self):
        with self.assertRaises(ValueError):
            recuperar_discursiva_05_2017(
                caminho_pdf=self.pdf,
                arquivo_origem="arquivo_incorreto.pdf",
                executavel_tesseract=(
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                ),
                pasta_saida=self.saida,
            )

if __name__ == "__main__":
    unittest.main()
