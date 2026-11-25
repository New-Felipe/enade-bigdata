"""Teste de integracao da recuperacao grafica no gerador canonico."""

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pymupdf

from extractor import gerar_canonicos


class TestGerarCanonicosRecuperacao(unittest.TestCase):

    def test_gera_40_questoes_com_alternativas_graficas(self):
        with tempfile.TemporaryDirectory() as temporario:
            base = Path(temporario)
            entrada = base / "questoes"
            saida = base / "questoes_canonicas"
            relatorio = base / "relatorio.json"
            prova = base / "prova.pdf"

            entrada.mkdir()

            # PDF sintetico com a pagina 37.
            with pymupdf.open() as documento:
                for _ in range(37):
                    documento.new_page(width=600, height=800)

                documento.save(prova)

            linhas_gabarito = []

            for tipo, quantidade in (
                ("objetiva", 35),
                ("discursiva", 5),
            ):
                for numero in range(1, quantidade + 1):
                    grafica = tipo == "objetiva" and numero == 33

                    texto = f"Enunciado da questao {numero}."

                    if grafica:
                        texto += (
                            " insere(17, 9)."
                            " Conteudo grafico extraido incorretamente."
                        )

                    questao = {
                        "numero_questao": numero,
                        "tipo_questao": tipo,
                        "texto": texto,
                        "alternativas": (
                            [
                                {
                                    "letra": letra,
                                    "texto": f"Alternativa {letra}.",
                                }
                                for letra in "ABCDE"
                            ]
                            if tipo == "objetiva" and not grafica
                            else []
                        ),
                        "origem": {
                            "arquivo": prova.name,
                            "pagina": 36 if grafica else 2,
                        },
                        "validacao_extracao": {
                            "status": (
                                "revisao_necessaria"
                                if grafica
                                else "extraido_textualmente"
                            ),
                        },
                    }

                    if grafica:
                        questao["pagina_final"] = 37

                    nome = f"{tipo}_{numero:02d}.json"

                    (entrada / nome).write_text(
                        json.dumps(questao, ensure_ascii=False),
                        encoding="utf-8",
                    )

                    if tipo == "objetiva":
                        resposta = "ANULADA" if grafica else "A"
                        linhas_gabarito.append(
                            f"QUEST\u00c3O {numero} {resposta}"
                        )
                    else:
                        linhas_gabarito.append(
                            f"QUEST\u00c3O DISCURSIVA {numero} ***"
                        )

            paginas_gabarito = [{
                "pagina": 1,
                "texto": "\n".join(linhas_gabarito),
            }]

            with (
                patch.object(gerar_canonicos, "ENTRADA", entrada),
                patch.object(gerar_canonicos, "SAIDA", saida),
                patch.object(gerar_canonicos, "RELATORIO", relatorio),
                patch.object(gerar_canonicos, "PROVA_PDF", prova),
                patch.object(
                    gerar_canonicos,
                    "extrair_paginas",
                    return_value=paginas_gabarito,
                ),
                redirect_stdout(StringIO()),
            ):
                gerar_canonicos.main()

            arquivos = list(saida.glob("*.json"))
            self.assertEqual(len(arquivos), 40)

            resultado = json.loads(
                relatorio.read_text(encoding="utf-8")
            )

            self.assertEqual(resultado["total_analisado"], 40)
            self.assertEqual(resultado["total_aprovado"], 40)
            self.assertEqual(resultado["total_pendente"], 0)

            identificador = (
                "enade-sistemas-de-informacao-2021-ce-obj-q33"
            )

            arquivo_33 = saida / f"{identificador}.json"
            self.assertTrue(arquivo_33.is_file())

            questao_33 = json.loads(
                arquivo_33.read_text(encoding="utf-8")
            )

            self.assertTrue(questao_33["anulada"])
            self.assertIsNone(questao_33["gabarito"])
            self.assertEqual(len(questao_33["alternativas"]), 5)
            self.assertTrue(
                questao_33["enunciado"].endswith("insere(17, 9).")
            )

            for letra, alternativa in zip(
                "ABCDE", questao_33["alternativas"]
            ):
                with self.subTest(letra=letra):
                    self.assertEqual(alternativa["letra"], letra)

                    imagem = saida / alternativa["imagem"]

                    self.assertTrue(imagem.is_file())
                    self.assertEqual(
                        imagem.read_bytes()[:8],
                        b"\x89PNG\r\n\x1a\n",
                    )


if __name__ == "__main__":
    unittest.main()
