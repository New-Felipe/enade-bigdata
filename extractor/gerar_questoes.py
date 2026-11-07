"""Gera os JSONs intermediarios da prova ENADE 2021."""

from pathlib import Path

from extractor.extractor import extrair_paginas
from extractor.segmenter import (
    mapear_questoes_prova,
    planejar_extracao_questoes,
    extrair_questoes_planejadas,
)
from extractor.gerador_json import salvar_questoes_json


PDF = Path(
    "data/raw/enade/2021/sistemas_de_informacao/"
    "enade_2021_sistemas_de_informacao_prova.pdf"
)

SAIDA = Path(
    "data/processed/enade/2021/"
    "sistemas_de_informacao/questoes"
)


def main():
    paginas = extrair_paginas(PDF)

    mapeadas = mapear_questoes_prova(paginas, str(PDF))

    planos = planejar_extracao_questoes(
        mapeadas,
        len(paginas),
    )

    resultado = extrair_questoes_planejadas(
        paginas=paginas,
        planos=planos,
        caminho_pdf=str(PDF),
        arquivo_origem=PDF.name,
        continuacoes={
            ("objetiva", 5): (11, 6),
            ("objetiva", 29): (33, 30),
        },
    )

    if resultado["falhas"] or len(resultado["extraidas"]) != 40:
        raise RuntimeError(
            "Extracao incompleta. Verifique as falhas antes de exportar."
        )

    arquivos = salvar_questoes_json(
        resultado["extraidas"],
        SAIDA,
    )

    print(f"JSONs gerados: {len(arquivos)}")
    print(f"Diretorio: {SAIDA}")
    print(f"Questoes para revisao: {len(resultado['revisar'])}")

    for item in resultado["revisar"]:
        print(
            f"Revisar: {item['tipo_questao']} "
            f"{item['numero_questao']:02d}"
        )


if __name__ == "__main__":
    main()
