"""Testes de alternativas distribuidas em duas colunas."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
class TestLocalizacaoDuasColunas(unittest.TestCase):
    def test_localiza_grupo_dividido_em_duas_colunas(self):
        with tempfile.TemporaryDirectory() as diretorio:
            pdf = Path(diretorio) / "prova.pdf"
            pdf.touch()
            documento = MagicMock()
            documento.__len__.return_value = 1
            pagina = MagicMock()
            documento.__getitem__.return_value = pagina
            marcadores = [
                ("A", 65.0, 326.7),
                ("B", 65.0, 496.8),
                ("C", 65.0, 666.8),
                ("D", 313.7, 326.7),
                ("E", 313.7, 496.8),
            ]
            pagina.get_text.return_value = [
                (x, y, x + 7, y + 10, letra, 0, 0, 0)
                for letra, x, y in marcadores
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
            grupo = grupos[0]
            self.assertEqual(
                [item["letra"] for item in grupo],
                list("ABCDE"),
            )
            self.assertEqual(
                [item["x"] for item in grupo],
                [65.0, 65.0, 65.0, 313.7, 313.7],
            )
if __name__ == "__main__":
    unittest.main()
