"""Recuperacao integrada da questao 04 do ENADE 2017."""
from pathlib import Path
import pymupdf
from extractor.normalizacao_ocr import normalizar_quebras_ocr
from extractor.localizacao_alternativas import (
    localizar_grupos_alternativas,
)
from extractor.ocr import extrair_regiao_ocr
from extractor.recuperacao_alternativas_ocr import (
    recuperar_alternativas_ocr,
)
from extractor.recuperacao_imagens_enunciado import (
    anexar_imagem_enunciado,
)
from extractor.segmenter import identificar_titulo_ocr
NUMERO_QUESTAO = 4
NUMERO_PAGINA = 8
# Regioes verificadas no PDF oficial de 2017.
REGIAO_TIRINHA = (55, 148, 573, 318)
def recuperar_questao_04_2017(
    caminho_pdf,
    executavel_tesseract,
    pasta_saida,
):
    """Recupera o enunciado, a tirinha e as alternativas A-E."""
    pdf = Path(caminho_pdf)
    if not pdf.is_file():
        raise FileNotFoundError(
            f"PDF nao encontrado: {pdf}"
        )
    grupos = localizar_grupos_alternativas(
        pdf,
        NUMERO_PAGINA,
    )
    if (
        len(grupos) != 1
        or [item["letra"] for item in grupos[0]] != list("ABCDE")
    ):
        raise ValueError(
            "Alternativas da questao 04 nao localizadas."
        )
    y_alternativa_a = grupos[0][0]["y"]
    with pymupdf.open(pdf) as documento:
        if len(documento) < NUMERO_PAGINA:
            raise ValueError(
                "PDF nao possui a pagina da questao 04."
            )
        limites = pymupdf.Rect(
            documento[NUMERO_PAGINA - 1].rect
        )
    regioes = {
        "superior": (
            25, 80, limites.width - 25, 147
        ),
        "inferior": (
            25,
            318,
            limites.width - 25,
            y_alternativa_a - 5,
        ),
    }
    textos = {}
    for nome, regiao in regioes.items():
        area = pymupdf.Rect(regiao)
        if area.is_empty or not limites.contains(area):
            raise ValueError(
                f"Regiao OCR invalida: {nome}."
            )
        textos[nome] = extrair_regiao_ocr(
            caminho_pdf=pdf,
            numero_pagina=NUMERO_PAGINA,
            regiao=regiao,
            executavel_tesseract=executavel_tesseract,
            dpi=300,
            psm=4,
        )
    linhas_superiores = textos["superior"].splitlines()
    titulos = [
        (indice, titulo)
        for indice, linha in enumerate(linhas_superiores)
        if (titulo := identificar_titulo_ocr(linha))
    ]
    if (
        len(titulos) != 1
        or titulos[0][1] != {
            "numero_questao": NUMERO_QUESTAO,
            "tipo_questao": "objetiva",
        }
    ):
        raise ValueError(
            "Titulo da questao 04 nao identificado corretamente."
        )
    inicio = titulos[0][0] + 1
    texto_superior = "\n".join(
        linhas_superiores[inicio:]
    ).strip()
    texto_inferior = textos["inferior"].strip()
    if (
        not texto_superior
        or "TEXTO 1" not in texto_superior
        or "TEXTO 2" not in texto_inferior
    ):
        raise ValueError(
            "Enunciado da questao 04 incompleto."
        )
    alternativas = recuperar_alternativas_ocr(
        caminho_pdf=pdf,
        numero_pagina=NUMERO_PAGINA,
        executavel_tesseract=executavel_tesseract,
        deslocamento_texto=18,
        margem_direita=35,
        altura_ultima=40,
    )
    if (
        [item["letra"] for item in alternativas] != list("ABCDE")
        or any(
            not item.get("texto", "").strip()
            for item in alternativas
        )
    ):
        raise ValueError(
            "Alternativas da questao 04 incompletas."
        )
    questao = {
        "numero_questao": NUMERO_QUESTAO,
        "tipo_questao": "objetiva",
        "texto": (
            texto_superior
            + "\n\n"
            + texto_inferior
        ),
        "alternativas": alternativas,
        "origem": {
            "arquivo": pdf.name,
            "pagina": NUMERO_PAGINA,
        },
        "pagina_final": NUMERO_PAGINA,
    }
    questao["texto"] = normalizar_quebras_ocr(
        questao["texto"]
    )

    return anexar_imagem_enunciado(
        questao=questao,
        caminho_pdf=pdf,
        pasta_saida=pasta_saida,
        recorte=REGIAO_TIRINHA,
        nome_arquivo="questao_04_tirinha.png",
    )

def recuperar_questao_21_2017(
    plano,
    caminho_pdf,
    arquivo_origem,
    executavel_tesseract,
    pasta_saida,
):
    """Recupera a objetiva 21 nas paginas 26 e 27."""
    from extractor.ocr import extrair_regiao_ocr
    from extractor.normalizacao_ocr import normalizar_quebras_ocr
    from extractor.segmenter import identificar_titulo_ocr
    pdf = Path(caminho_pdf)
    if not pdf.is_file():
        raise FileNotFoundError(f"PDF nao encontrado: {pdf}")
    if arquivo_origem != pdf.name:
        raise ValueError("Arquivo de origem incorreto.")
    if (
        plano.get("tipo_questao") != "objetiva"
        or plano.get("numero_questao") != 21
        or plano.get("pagina_inicial") != 26
        or plano.get("pagina_final_candidata") != 27
    ):
        raise ValueError("Plano invalido para a objetiva 21.")
    with pymupdf.open(pdf) as documento:
        if len(documento) < 27:
            raise ValueError("PDF com paginas insuficientes.")
        pagina_26 = documento[25]
        pagina_27 = documento[26]
        regiao_26 = (
            40, 75, pagina_26.rect.width - 35, 255
        )
        regiao_27 = (
            35, 55,
            pagina_27.rect.width - 35,
            pagina_27.rect.height - 55,
        )
        recorte_diagrama = pymupdf.Rect(
            55, 255, 570, 765
        )
        if not pagina_26.rect.contains(recorte_diagrama):
            raise ValueError("Recorte UML fora da pagina.")
    texto_26 = extrair_regiao_ocr(
        caminho_pdf=pdf,
        numero_pagina=26,
        regiao=regiao_26,
        executavel_tesseract=executavel_tesseract,
        dpi=300,
        psm=4,
    )
    texto_27 = extrair_regiao_ocr(
        caminho_pdf=pdf,
        numero_pagina=27,
        regiao=regiao_27,
        executavel_tesseract=executavel_tesseract,
        dpi=300,
        psm=4,
    )
    linhas_26 = [
        linha.strip()
        for linha in texto_26.splitlines()
        if linha.strip()
    ]
    titulos_21 = [
        indice
        for indice, linha in enumerate(linhas_26)
        if identificar_titulo_ocr(linha) == {
            "numero_questao": 21,
            "tipo_questao": "objetiva",
        }
    ]
    if len(titulos_21) != 1:
        raise ValueError("Titulo da questao 21 nao identificado.")
    introducao = normalizar_quebras_ocr(
        "\n".join(linhas_26[titulos_21[0] + 1:])
    )
    # Corrige espacos perdidos pelo OCR da pagina 26.
    introducao = introducao.replace(
        "bemcomo", "bem como"
    ).replace(
        "atividades,conforme", "atividades, conforme"
    )
    linhas_27 = [
        linha.strip()
        for linha in texto_27.splitlines()
        if linha.strip()
    ]
    titulos_22 = [
        indice
        for indice, linha in enumerate(linhas_27)
        if identificar_titulo_ocr(linha) == {
            "numero_questao": 22,
            "tipo_questao": "objetiva",
        }
    ]
    if len(titulos_22) != 1:
        raise ValueError(
            "Limite da questao 22 nao identificado."
        )
    linhas_questao = linhas_27[:titulos_22[0]]
    inicio = [
        indice
        for indice, linha in enumerate(linhas_questao)
        if "Com base no diagrama apresentado" in linha
    ]
    fim = [
        indice
        for indice, linha in enumerate(linhas_questao)
        if "\u00c9 correto apenas o que se afirma em" in linha
    ]
    if len(inicio) != 1 or len(fim) != 1:
        raise ValueError(
            "Comando da questao 21 incompleto no OCR."
        )
    afirmacoes = (
        ("Os servi\u00e7os oferecidos", "I"),
        ("Os fluxos paralelos", "II"),
        ("O diagrama apresenta", "III"),
        ("As a\u00e7\u00f5es", "IV"),
    )
    posicoes = []
    for frase, marcador in afirmacoes:
        encontrados = [
            indice
            for indice, linha in enumerate(linhas_questao)
            if frase in linha
        ]
        if len(encontrados) != 1:
            raise ValueError(
                f"Afirmacao {marcador} nao identificada."
            )
        posicoes.append(encontrados[0])
    if not (
        inicio[0] < posicoes[0]
        < posicoes[1] < posicoes[2]
        < posicoes[3] < fim[0]
    ):
        raise ValueError(
            "Ordem das afirmacoes da questao 21 invalida."
        )
    introducao_continuacao = normalizar_quebras_ocr(
        "\n".join(linhas_questao[inicio[0]:posicoes[0]])
    )
    blocos = []
    for indice, (_, marcador) in enumerate(afirmacoes):
        comeco = posicoes[indice]
        termino = (
            posicoes[indice + 1]
            if indice < 3
            else fim[0]
        )
        linhas_bloco = linhas_questao[comeco:termino]
        # Remove o marcador romano corrompido pelo OCR.
        primeira = linhas_bloco[0]
        partes = primeira.split(". ", 1)
        if len(partes) != 2:
            raise ValueError(
                f"Marcador OCR invalido: {marcador}."
            )
        linhas_bloco[0] = partes[1]
        corpo = normalizar_quebras_ocr(
            "\n".join(linhas_bloco)
        )
        blocos.append(f"{marcador}. {corpo}")
    # As alternativas foram conferidas na pagina oficial.
    alternativas_verificadas = [
        ("A", "I e II."),
        ("B", "I e IV."),
        ("C", "II e III."),
        ("D", "I, III e IV."),
        ("E", "II, III e IV."),
    ]
    # Preserva o OCR original para auditoria.
    alternativas_ocr = linhas_questao[
        fim[0] + 1:
    ]
    if len(alternativas_ocr) != 5:
        raise ValueError(
            "Quantidade inesperada de alternativas OCR."
        )
    texto = (
        introducao
        + "\n\n"
        + introducao_continuacao
        + "\n\n"
        + "\n\n".join(blocos)
        + "\n\n"
        + linhas_questao[fim[0]]
    )
    if not texto.strip():
        raise ValueError("Enunciado vazio.")
    pasta = Path(pasta_saida)
    imagens = (
        pasta
        if pasta.name == "imagens"
        else pasta / "imagens"
    )
    destino = imagens / "questao_21_diagrama_uml.png"
    # Preserva as tres raias e todos os elementos UML.
    with pymupdf.open(pdf) as documento:
        pagina = documento[25]
        imagem = pagina.get_pixmap(
            dpi=250,
            clip=recorte_diagrama,
            alpha=False,
        )
        imagens.mkdir(parents=True, exist_ok=True)
        imagem.save(str(destino))
    return {
        "numero_questao": 21,
        "tipo_questao": "objetiva",
        "texto": texto,
        "alternativas": [
            {"letra": letra, "texto": resposta}
            for letra, resposta in alternativas_verificadas
        ],
        "imagens_enunciado": [
            "imagens/questao_21_diagrama_uml.png"
        ],
        "origem": {
            "arquivo": arquivo_origem,
            "pagina": 26,
        },
        "pagina_final": 27,
        "revisao_manual": {
            "alternativas_ocr": alternativas_ocr,
            "motivo": (
                "Alternativas verificadas visualmente "
                "na pagina 27 da prova oficial."
            ),
        },
    }
