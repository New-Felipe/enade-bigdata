"""Interpretacao do gabarito oficial do ENADE."""

import re


def interpretar_gabarito(texto):
    """Converte o texto do gabarito em registros por tipo e numero."""

    padrao = re.compile(
        r"^QUESTÃO\s+(?:(DISCURSIVA)\s+)?(\d+)\s+"
        r"([A-E]|\*{3}|ANULADA)$",
        re.IGNORECASE,
    )

    padrao_tabular = re.compile(
        r"^(\d+)\s+([A-E]|\*{3}|ANULADA)$",
        re.IGNORECASE,
    )
    registros = {}

    for linha in texto.splitlines():
        linha = linha.strip()
        correspondencia = padrao.fullmatch(linha)
        if correspondencia:
            discursiva, numero, resposta = correspondencia.groups()
            tipo = "discursiva" if discursiva else "objetiva"
        else:
            correspondencia = padrao_tabular.fullmatch(linha)
            if not correspondencia:
                continue
            numero, resposta = correspondencia.groups()
            tipo = "objetiva"
        numero = int(numero)
        resposta = resposta.upper()

        chave = (tipo, numero)

        if chave in registros:
            raise ValueError(
                f"Questao duplicada no gabarito: {tipo} {numero}"
            )

        registros[chave] = {
            "gabarito": resposta if resposta in "ABCDE" else None,
            "anulada": resposta == "ANULADA",
        }

    if not registros:
        raise ValueError("Nenhuma questao encontrada no gabarito.")

    return registros
