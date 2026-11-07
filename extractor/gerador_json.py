"""Exportacao das questoes extraidas para arquivos JSON."""

import json
from pathlib import Path


def salvar_questoes_json(questoes, diretorio_saida):
    """Salva cada questao em um arquivo JSON independente."""

    destino = Path(diretorio_saida)
    destino.mkdir(parents=True, exist_ok=True)

    arquivos = []

    for questao in questoes:
        numero = questao["numero_questao"]
        tipo = questao["tipo_questao"]
        alternativas = questao["alternativas"]

        revisar = (
            tipo == "objetiva"
            and len(alternativas) != 5
        )

        documento = {
            **questao,
            "validacao_extracao": {
                "status": (
                    "revisao_necessaria"
                    if revisar
                    else "extraido_textualmente"
                ),
                "quantidade_alternativas": len(alternativas),
            },
        }

        nome_arquivo = f"{tipo}_{numero:02d}.json"
        caminho = destino / nome_arquivo

        with caminho.open("w", encoding="utf-8") as arquivo:
            json.dump(
                documento,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

        arquivos.append(caminho)

    return arquivos
