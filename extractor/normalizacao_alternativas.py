"""Normalizacao de alternativas com algarismos romanos no ENADE 2017."""

import re


SIMBOLOS_ROMANOS = {
    "/": "I",
    "//": "II",
    "///": "III",
    "/s": "IV",
}

PADRAO_ALTERNATIVA = re.compile(
    r"(?:/{1,3}|/s)"
    r"(?:,\s*(?:/{1,3}|/s))*"
    r"\s+e\s+"
    r"(?:/{1,3}|/s)\."
)


def normalizar_alternativa_romana(texto):
    """Corrige apenas alternativas com estrutura romana reconhecida."""

    if not isinstance(texto, str):
        raise ValueError("Texto da alternativa invalido.")

    normalizado = (
        texto.strip()
        .replace("\u0355", ",")
        .replace("\u0358", ".")
        .replace("\u011e", "e")
    )

    if not PADRAO_ALTERNATIVA.fullmatch(normalizado):
        raise ValueError(
            f"Formato de alternativa nao reconhecido: {texto!r}"
        )

    return re.sub(
        r"/s|/{1,3}",
        lambda resultado: SIMBOLOS_ROMANOS[resultado.group()],
        normalizado,
    )
