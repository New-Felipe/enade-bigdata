"""Testes do gerador de questoes canonicas ENADE."""

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from extractor import gerar_canonicos


class TestGerarCanonicos(unittest.TestCase):

    def test_gera_39_questoes_e_registra_pendencia(self):
        with tempfile.TemporaryDirectory() as temporario:
            base = Path(temporario)
            entrada = base / "questoes"
            saida = base / "questoes_canonicas"
            relatorio = base / "relatorio.json"

            entrada.mkdir()

            linhas_gabarito = []

            for tipo, quantidade in (
                ("objetiva", 35),
                ("discursiva", 5),
            ):
                for numero in range(1, quantidade + 1):
                    pendente = tipo == "objetiva" and numero == 33

                    questao = {
                        "numero_questao": numero,
                        "tipo_questao": tipo,
                        "texto": f"Enunciado da questao {numero}.",
                        "alternativas": (
                            [
                                {
                                    "letra": letra,
                                    "texto": f"Alternativa {letra}.",
                                }
                                for letra in "ABCDE"
                            ]
                            if tipo == "objetiva" and not pendente
                            else []
                        ),
                        "origem": {
                            "arquivo": "prova.pdf",
                            "pagina": 2,
                        },
                        "validacao_extracao": {
                            "status": (
                                "revisao_necessaria"
                                if pendente
                                else "extraido_textualmente"
                            ),
                        },
                    }

                    nome = f"{tipo}_{numero:02d}.json"
                    (entrada / nome).write_text(
                        json.dumps(questao, ensure_ascii=False),
                        encoding="utf-8",
                    )

                    if tipo == "objetiva":
                        resposta = "ANULADA" if pendente else "A"
                        linhas_gabarito.append(
                            f"QUESTÃO {numero} {resposta}"
                        )
                    else:
                        linhas_gabarito.append(
                            f"QUESTÃO DISCURSIVA {numero} ***"
                        )

            paginas_gabarito = [{
                "pagina": 1,
                "texto": "\n".join(linhas_gabarito),
            }]

            with (
                patch.object(gerar_canonicos, "ENTRADA", entrada),
                patch.object(gerar_canonicos, "SAIDA", saida),
                patch.object(gerar_canonicos, "RELATORIO", relatorio),
                patch.object(
                    gerar_canonicos,
                    "extrair_paginas",
                    return_value=paginas_gabarito,
                ),
                redirect_stdout(StringIO()),
            ):
                gerar_canonicos.main()

            arquivos = list(saida.glob("*.json"))
            self.assertEqual(len(arquivos), 39)

            dados_relatorio = json.loads(
                relatorio.read_text(encoding="utf-8")
            )

            self.assertEqual(
                dados_relatorio["total_analisado"], 40
            )
            self.assertEqual(
                dados_relatorio["total_aprovado"], 39
            )
            self.assertEqual(
                dados_relatorio["total_pendente"], 1
            )
            self.assertEqual(
                dados_relatorio["pendentes"][0]["arquivo"],
                "objetiva_33.json",
            )

            ids = {
                json.loads(
                    arquivo.read_text(encoding="utf-8")
                )["id"]
                for arquivo in arquivos
            }

            self.assertEqual(len(ids), 39)
            self.assertIn(
                "enade-formacao-geral-2021-fg-obj-q01",
                ids,
            )
            self.assertIn(
                "enade-sistemas-de-informacao-2021-ce-disc-q03",
                ids,
            )
            self.assertNotIn(
                "enade-sistemas-de-informacao-2021-ce-obj-q33",
                ids,
            )


if __name__ == "__main__":
    unittest.main()
