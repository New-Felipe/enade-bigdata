"""Testes de alternativas com espacamento vertical variavel."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
class TestLocalizacaoEspacamento(unittest.TestCase):
    def test_localiza_alternativas_com_espacamento_maior(self):
        with tempfile.TemporaryDirectory() as diretorio:
            pdf = Path(diretorio) / "prova.pdf"
            pdf.touch()
            documento = MagicMock()
            documento.__len__.return_value = 1
            pagina = MagicMock()
            documento.__getitem__.return_value = pagina
            posicoes = [
                200.0,
                251.7,
                317.8,
                383.9,
                450.1,
            ]
            pagina.get_text.return_value = [
                (60.4, y, 67.4, y + 10, letra, 0, 0, 0)
                for letra, y in zip("ABCDE", posicoes)
            ]
            with patch(
                "extractor.localizacao_alternativas.pymupdf.open"
            ) as abrir:
                abrir.return_value.__enter__.return_value = (
                    documento
                )
                grupos = localizar_grupos_alternativas(
                    pdf,
                    1,
                )
            self.assertEqual(len(grupos), 1)
            self.assertEqual(
                [item["letra"] for item in grupos[0]],
                list("ABCDE"),
            )
if __name__ == "__main__":
    unittest.main()
