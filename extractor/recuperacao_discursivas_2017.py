"""Recuperadores das questoes discursivas do ENADE 2017."""
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

def recuperar_discursiva_05_2017(
    caminho_pdf,
    arquivo_origem,
    executavel_tesseract,
    pasta_saida,
    plano=None,
):
    """Recupera o enunciado e a tabela da pagina 15."""
    pdf = Path(caminho_pdf)
    if not pdf.is_file():
        raise FileNotFoundError(
            f"PDF nao encontrado: {pdf}"
        )
    if arquivo_origem != pdf.name:
        raise ValueError(
            "Nome do arquivo de origem nao corresponde ao PDF."
        )
    if plano is not None:
        if (
            plano.get("numero_questao") != 5
            or plano.get("tipo_questao") != "discursiva"
            or plano.get("pagina_inicial") != 15
        ):
            raise ValueError(
                "Plano invalido para a discursiva 05."
            )
    with pymupdf.open(pdf) as documento:
        if len(documento) < 15:
            raise ValueError(
                "A prova nao possui a pagina 15."
            )
        pagina = documento[14]
        regiao_texto = (
            25,
            55,
            pagina.rect.width - 25,
            pagina.rect.height - 55,
        )
        recorte_tabela = pymupdf.Rect(
            98, 406, 530, 645
        )
        if not pagina.rect.contains(recorte_tabela):
            raise ValueError(
                "Recorte da tabela fora da pagina."
            )
    texto_ocr = extrair_regiao_ocr(
        caminho_pdf=pdf,
        numero_pagina=15,
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
        "numero_questao": 5,
        "tipo_questao": "discursiva",
    }
    if len(titulos) != 1 or titulos[0][1] != esperado:
        raise ValueError(
            "Titulo OCR nao corresponde a discursiva 05."
        )
    inicio = titulos[0][0] + 1
    corpo = linhas[inicio:]
    # Elimina eventual conteudo de rascunho ou rodape.
    for indice, linha in enumerate(corpo):
        normalizada = linha.strip().upper()
        if (
            normalizada.startswith("RASCUNHO")
            or normalizada.startswith("AREA LIVRE")
            or normalizada.startswith("\u00c1REA LIVRE")
            or normalizada.startswith("SISTEMAS DE INFORMA")
        ):
            corpo = corpo[:indice]
            break
    texto = normalizar_quebras_ocr(
        "\n".join(corpo)
    )
    # Corrige erros de OCR conferidos na pagina 15 da prova.
    # Mantem estas revisoes restritas a discursiva 05 de 2017.
    correcoes = (
        (
            "realiza\u00e7\u00e3o, O hor\u00e1rio",
            "realiza\u00e7\u00e3o, o hor\u00e1rio",
        ),
        (
            "\ne o equipamento utilizado,",
            "\n\u2022 o equipamento utilizado,",
        ),
        (
            "\ne otipo de alvo",
            "\n\u2022 o tipo de alvo",
        ),
        (
            "; e a posi\u00e7\u00e3o do atirador",
            ";\n\u2022 a posi\u00e7\u00e3o do atirador",
        ),
        (
            "Pistola 5O m",
            "Pistola 50 m",
        ),
    )
    for original, corrigido in correcoes:
        if texto.count(original) != 1:
            raise ValueError(
                "Trecho OCR esperado nao encontrado "
                f"de forma unica: {original!r}"
            )
        texto = texto.replace(original, corrigido, 1)
    # Reconstrucao textual da tabela conferida no PDF oficial.
    # Preserva a representacao visual separadamente como imagem.
    inicio_tabela = (
        "Competi\u00e7\u00f5es masculinas "
        "Competi\u00e7\u00f5es femininas"
    )
    fim_tabela = "As competi\u00e7\u00f5es dessa modalidade"
    if (
        texto.count(inicio_tabela) != 1
        or texto.count(fim_tabela) != 1
    ):
        raise ValueError(
            "Nao foi possivel delimitar a tabela da discursiva 05."
        )
    inicio = texto.index(inicio_tabela)
    fim = texto.index(fim_tabela, inicio)
    bloco_ocr = texto[inicio:fim]
    termos_esperados = (
        "Pistola de ar 10m",
        "Carabina de ar 10 m",
        "Pistola r\u00e1pida 25 m",
        "Pistola 50 m",
        "Carabina deitado 50 m",
        "Carabina tr\u00eas posi\u00e7\u00f5es 50 m",
        "Skeet",
        "Fossa ol\u00edmpica",
        "Fossa ol\u00edmpica dupla",
    )
    faltantes = [
        termo for termo in termos_esperados
        if termo not in bloco_ocr
    ]
    if faltantes:
        raise ValueError(
            "Tabela OCR incompleta; revisao necessaria: "
            + ", ".join(faltantes)
        )
    tabela = (
        "| Competi\u00e7\u00f5es masculinas | Competi\u00e7\u00f5es femininas |\n"
        "| --- | --- |\n"
        "| Pistola de ar 10 m | Pistola de ar 10 m |\n"
        "| Carabina de ar 10 m | Carabina de ar 10 m |\n"
        "| Pistola r\u00e1pida 25 m | Pistola 25 m |\n"
        "| Pistola 50 m | Carabina tr\u00eas posi\u00e7\u00f5es 50 m |\n"
        "| Carabina deitado 50 m | Skeet |\n"
        "| Carabina tr\u00eas posi\u00e7\u00f5es 50 m | Fossa ol\u00edmpica |\n"
        "| Skeet | |\n"
        "| Fossa ol\u00edmpica | |\n"
        "| Fossa ol\u00edmpica dupla | |"
    )
    texto = (
        texto[:inicio].rstrip()
        + "\n\n"
        + tabela
        + "\n\n"
        + texto[fim:]
    )
    if not texto.strip():
        raise ValueError(
            "Enunciado vazio apos o OCR."
        )
    # Confere as partes essenciais da questao.
    verificacoes = {
        "introducao": "Olimp\u00edadas de 2016",
        "tabela masculina": "Competi\u00e7\u00f5es masculinas",
        "tabela feminina": "Competi\u00e7\u00f5es femininas",
        "ultima competicao": "Fossa ol\u00edmpica dupla",
        "solicitacao UML": "diagrama de classe da UML",
    }
    for nome, trecho in verificacoes.items():
        if trecho.casefold() not in texto.casefold():
            raise ValueError(
                f"Conteudo OCR incompleto: {nome}."
            )
    destino = (
        Path(pasta_saida)
        / "discursiva_05_tabela_competicoes.png"
    )
    # Renderiza a tabela inteira, incluindo linhas vetoriais.
    # O recorte nao depende de imagens incorporadas no PDF.
    with pymupdf.open(pdf) as documento:
        pagina = documento[14]
        imagem = pagina.get_pixmap(
            dpi=300,
            clip=recorte_tabela,
            alpha=False,
        )
        destino.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        imagem.save(str(destino))
    return {
        "numero_questao": 5,
        "tipo_questao": "discursiva",
        "texto": texto,
        "alternativas": [],
        "imagens_enunciado": [
            "imagens/discursiva_05_tabela_competicoes.png"
        ],
        "origem": {
            "arquivo": arquivo_origem,
            "pagina": 15,
        },
        "pagina_final": 15,
    }
