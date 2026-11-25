"""Correcoes controladas de erros de reconhecimento por OCR."""

import re


PADRAO_AFIRMACAO = re.compile(
    r"^(\s*)(?:[Il1|]{1,3}|IV)\.(?=\s)"
)


def corrigir_numeracao_afirmacoes(texto, numeracao_pdf):
    """Corrige marcadores do OCR usando numeracao verificada no PDF.

    Recebe somente o enunciado, sem as alternativas.
    A numeracao_pdf deve ser obtida ou conferida no documento original.
    """

    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("Texto do enunciado invalido.")

    if not isinstance(numeracao_pdf, (list, tuple)):
        raise ValueError("Numeracao do PDF invalida.")

    if list(numeracao_pdf) != ["I", "II", "III", "IV"]:
        raise ValueError(
            "Numeracao nao corresponde ao padrao I-IV validado."
        )

    linhas = texto.splitlines()

    indices = [
        indice
        for indice, linha in enumerate(linhas)
        if PADRAO_AFIRMACAO.match(linha)
    ]

    if len(indices) != len(numeracao_pdf):
        raise ValueError(
            "Quantidade de afirmacoes do OCR difere do PDF."
        )

    for indice, romano in zip(indices, numeracao_pdf):
        linhas[indice] = PADRAO_AFIRMACAO.sub(
            lambda resultado: f"{resultado.group(1)}{romano}.",
            linhas[indice],
            count=1,
        )

    return "\n".join(linhas)
