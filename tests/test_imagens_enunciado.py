"""Testes do suporte a imagens no enunciado canonico."""
import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from extractor.conversor import converter_questao_canonica
class TestImagensEnunciado(unittest.TestCase):
    def setUp(self):
        self.imagem = "imagens/questao_04_tirinha.png"
        self.questao = {
            "numero_questao": 4,
            "tipo_questao": "objetiva",
            "texto": "Sobre a televisao, considere a tirinha.",
            "alternativas": [
                {"letra": letra, "texto": f"Alternativa {letra}"}
                for letra in "ABCDE"
            ],
            "gabarito": "B",
            "anulada": False,
            "origem": {
                "arquivo": "prova.pdf",
                "pagina": 8,
            },
            "imagens_enunciado": [self.imagem],
        }
    def test_conversor_preserva_imagens_enunciado(self):
        documento = converter_questao_canonica(
            self.questao, 2021
        )
        self.assertEqual(
            documento.get("imagens_enunciado"),
            [self.imagem],
        )
    def test_schema_aceita_imagens_enunciado(self):
        schema = json.loads(
            Path(
                "docs/schemas/questao.schema.json"
            ).read_text(encoding="utf-8")
        )
        documento = converter_questao_canonica(
            self.questao, 2021
        )
        documento["imagens_enunciado"] = [self.imagem]
        erros = list(
            Draft202012Validator(schema).iter_errors(documento)
        )
        self.assertEqual(
            [],
            [erro.message for erro in erros],
        )

    def test_questao_sem_imagens_continua_valida(self):
        questao = dict(self.questao)
        del questao["imagens_enunciado"]
        documento = converter_questao_canonica(questao, 2021)
        self.assertNotIn("imagens_enunciado", documento)
        schema = json.loads(
            Path("docs/schemas/questao.schema.json")
            .read_text(encoding="utf-8")
        )
        Draft202012Validator(schema).validate(documento)
    def test_rejeita_lista_de_imagens_vazia(self):
        self._verificar_imagens_invalidas([])
    def test_rejeita_referencia_sem_conteudo(self):
        self._verificar_imagens_invalidas(["   "])
    def test_rejeita_imagens_duplicadas(self):
        self._verificar_imagens_invalidas([
            self.imagem,
            self.imagem,
        ])
    def _verificar_imagens_invalidas(self, imagens):
        schema = json.loads(
            Path("docs/schemas/questao.schema.json")
            .read_text(encoding="utf-8")
        )
        documento = converter_questao_canonica(
            self.questao, 2021
        )
        documento["imagens_enunciado"] = imagens
        erros = list(
            Draft202012Validator(schema).iter_errors(documento)
        )
        self.assertTrue(
            erros,
            "O schema deveria rejeitar imagens invalidas.",
        )

if __name__ == "__main__":
    unittest.main()
