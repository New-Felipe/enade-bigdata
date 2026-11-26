"""Normalizacao conservadora de quebras artificiais do OCR."""
import re
def normalizar_quebras_ocr(texto):
    """Une linhas artificiais preservando paragrafos e titulos."""
    if not isinstance(texto, str):
        raise TypeError("O texto deve ser uma string.")
    texto = texto.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not texto:
        return ""
    blocos = re.split(r"\n\s*\n+", texto)
    paragrafos = []
    for bloco in blocos:
        linhas = [
            linha.strip()
            for linha in bloco.splitlines()
            if linha.strip()
        ]
        if not linhas:
            continue
        # Quebras simples dentro de um bloco sao tratadas
        # como continuacao da mesma linha de texto.
        paragrafo = " ".join(linhas)
        if paragrafos:
            anterior = paragrafos[-1]
            titulo = re.fullmatch(
                r"TEXTO\s+\d+",
                anterior,
                flags=re.IGNORECASE,
            )
            frase_incompleta = not re.search(
                r"[.!?;:]$",
                anterior,
            )
            continua_minuscula = bool(
                re.match(r"^[a-zà-ÿ]", paragrafo)
            )
            if (
                not titulo
                and frase_incompleta
                and continua_minuscula
            ):
                paragrafos[-1] = anterior + " " + paragrafo
                continue
        paragrafos.append(paragrafo)
    return "\n\n".join(paragrafos)
