"""Recuperacao da questao discursiva 04 do ENADE 2017."""
from pathlib import Path
import re
import unicodedata
import pymupdf
from extractor.normalizacao_ocr import normalizar_quebras_ocr
from extractor.ocr import extrair_regiao_ocr
from extractor.segmenter import identificar_titulo_ocr
def recuperar_discursiva_04_2017(
    plano,
    caminho_pdf,
    arquivo_origem,
    executavel_tesseract,
    pasta_saida,
):
    """Recupera enunciado, itens a/b e figura do cafezal."""
    if (
        plano.get("numero_questao") != 4
        or plano.get("tipo_questao") != "discursiva"
        or plano.get("pagina_inicial") != 14
        or plano.get("pagina_final_candidata") != 14
    ):
        raise ValueError(
            "Plano invalido para a discursiva 04 de 2017."
        )
    pdf = Path(caminho_pdf)
    if not pdf.is_file():
        raise FileNotFoundError(
            f"PDF nao encontrado: {pdf}"
        )
    with pymupdf.open(pdf) as documento:
        if len(documento) < 14:
            raise ValueError(
                "A prova nao possui a pagina 14."
            )
        pagina = documento[13]
        limites = pymupdf.Rect(pagina.rect)
    regiao_texto = (
        25,
        55,
        limites.width - 25,
        limites.height - 55,
    )
    texto_ocr = extrair_regiao_ocr(
        caminho_pdf=pdf,
        numero_pagina=14,
        regiao=regiao_texto,
        executavel_tesseract=executavel_tesseract,
        dpi=300,
        psm=4,
    )
    linhas = texto_ocr.splitlines()
    titulos = [
        (indice, titulo)
        for indice, linha in enumerate(linhas)
        if (titulo := identificar_titulo_ocr(linha))
    ]
    esperado = {
        "numero_questao": 4,
        "tipo_questao": "discursiva",
    }
    if (
        len(titulos) != 1
        or titulos[0][1] != esperado
    ):
        raise ValueError(
            "Titulo OCR nao corresponde a discursiva 04."
        )
    # Ignora o cabecalho anterior ao titulo da questao.
    inicio = titulos[0][0] + 1
    corpo = linhas[inicio:]
    def normalizar_linha(linha):
        decomposicao = unicodedata.normalize(
            "NFKD",
            linha.strip().upper(),
        )
        return "".join(
            caractere
            for caractere in decomposicao
            if not unicodedata.combining(caractere)
        )
    # Exclui o quadro de rascunho e o espaco livre.
    limite_corpo = len(corpo)
    for indice, linha in enumerate(corpo):
        normalizada = normalizar_linha(linha)
        if (
            normalizada.startswith("RASCUNHO")
            or normalizada.startswith("AREA LIVRE")
        ):
            limite_corpo = indice
            break
    corpo = corpo[:limite_corpo]
    # Confere que os dois itens foram recuperados.
    tem_item_a = any(
        re.match(r"^\s*a\)", linha, re.IGNORECASE)
        for linha in corpo
    )
    tem_item_b = any(
        re.match(r"^\s*b\)", linha, re.IGNORECASE)
        for linha in corpo
    )
    if not (tem_item_a and tem_item_b):
        raise ValueError(
            "Itens a e b incompletos na discursiva 04."
        )
    texto = normalizar_quebras_ocr(
        "\n".join(corpo)
    )
    # Preserva a separacao dos itens discursivos da prova.
    # Correcao restrita a discursiva 04 do ENADE 2017.
    texto, quantidade = re.subn(
        r"[ \t]+b\)[ \t]+(?=Escreva o algoritmo\b)",
        "\nb) ",
        texto,
        count=1,
    )
    if quantidade != 1 and "\nb) Escreva o algoritmo" not in texto:
        raise ValueError(
            "Nao foi possivel separar o item b da discursiva 04."
        )
    if not texto.strip():
        raise ValueError(
            "Enunciado vazio apos a recuperacao OCR."
        )
    # Inclui a grade vetorial e os cafeeiros no recorte.
    recorte_figura = pymupdf.Rect(
        200, 160, 430, 300
    )
    destino = (
        Path(pasta_saida)
        / "discursiva_04_cafezal.png"
    )
    with pymupdf.open(pdf) as documento:
        pagina = documento[13]
        if not pagina.rect.contains(recorte_figura):
            raise ValueError(
                "Recorte da figura fora dos limites da pagina."
            )
        imagem = pagina.get_pixmap(
            dpi=300,
            clip=recorte_figura,
            alpha=False,
        )
        destino.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        imagem.save(str(destino))
    return {
        "numero_questao": 4,
        "tipo_questao": "discursiva",
        "texto": texto,
        "alternativas": [],
        "imagens_enunciado": [
            "imagens/discursiva_04_cafezal.png"
        ],
        "origem": {
            "arquivo": arquivo_origem,
            "pagina": 14,
        },
        "pagina_final": 14,
    }
