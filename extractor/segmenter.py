"""Funcoes para identificar questoes nas provas do ENADE."""

import re
import unicodedata

from extractor.extractor import extrair_colunas, limpar_texto_pagina

PADRAO_QUESTAO = re.compile(
    r"^QUESTAO\s+(?:(DISCURSIVA)\s+)?(\d{1,2})$",
    re.IGNORECASE,
)


def normalizar_texto(texto):
    """Remove acentos para facilitar a identificacao de titulos."""
    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    ).upper()

def identificar_titulo(linha):
    """Identifica o numero e o tipo de uma questao."""
    linha_normalizada = normalizar_texto(linha.strip())
    resultado = PADRAO_QUESTAO.fullmatch(linha_normalizada)

    if not resultado:
        return None

    return {
        "numero_questao": int(resultado.group(2)),
        "tipo_questao": (
            "discursiva" if resultado.group(1) else "objetiva"
        ),
    }

def separar_alternativas(texto):
    """Separa alternativas A-E preservando texto-base e continuacoes."""
    linhas = texto.splitlines()

    # Remove areas destinadas a rascunho ou respostas em branco.
    marcadores_fim = {"AREA LIVRE", "RASCUNHO"}

    for indice, linha in enumerate(linhas):
        linha_normalizada = normalizar_texto(linha).strip()

        if linha_normalizada in marcadores_fim:
            linhas = linhas[:indice]
            break

    padrao = re.compile(r"^\s*([A-E])\s+(.+)$")

    candidatos = []

    for indice, linha in enumerate(linhas):
        resultado = padrao.match(linha)
        if resultado:
            candidatos.append((indice, resultado.group(1)))

    sequencias = []

    for posicao, (indice, letra) in enumerate(candidatos):
        if letra != "A":
            continue

        sequencia = [(indice, letra)]

        for proximo_indice, proxima_letra in candidatos[posicao + 1:]:
            esperado = chr(ord(sequencia[-1][1]) + 1)

            if proxima_letra == esperado:
                sequencia.append((proximo_indice, proxima_letra))

            if len(sequencia) == 5:
                sequencias.append(sequencia)
                break

    if not sequencias:
        return {
            "texto": "\n".join(linhas).strip(),
            "alternativas": [],
        }

    # Prioriza a ultima sequencia completa identificada.
    marcadores = sequencias[-1]
    inicio = marcadores[0][0]

    texto_principal = "\n".join(linhas[:inicio]).strip()
    alternativas = []

    for posicao, (indice, letra) in enumerate(marcadores):
        fim = (
            marcadores[posicao + 1][0]
            if posicao + 1 < len(marcadores)
            else len(linhas)
        )

        conteudo = linhas[indice:fim]
        primeira_linha = padrao.match(conteudo[0]).group(2)

        continuacao = [
            linha.strip()
            for linha in conteudo[1:]
            if linha.strip()
        ]

        alternativas.append({
            "letra": letra,
            "texto": " ".join(
                [primeira_linha.strip()] + continuacao
            ),
        })

    return {
        "texto": texto_principal,
        "alternativas": alternativas,
    }

    # Evita retornar alternativas incompletas como resultado valido.
    if [letra for _, letra in marcadores] != list("ABCDE"):
        return {
            "texto": texto.strip(),
            "alternativas": [],
        }

    inicio_alternativas = marcadores[0][0]

    texto_principal = "\n".join(
        linhas[:inicio_alternativas]
    ).strip()

    alternativas = []

    for posicao, (indice, letra) in enumerate(marcadores):
        fim = (
            marcadores[posicao + 1][0]
            if posicao + 1 < len(marcadores)
            else len(linhas)
        )

        conteudo = linhas[indice:fim]

        primeira_linha = padrao.match(conteudo[0]).group(2)

        continuacao = [
            linha.strip()
            for linha in conteudo[1:]
            if linha.strip()
        ]

        alternativas.append({
            "letra": letra,
            "texto": " ".join(
                [primeira_linha.strip()] + continuacao
            ),
        })

    return {
        "texto": texto_principal,
        "alternativas": alternativas,
    }

def segmentar_questao_em_paginas(
    paginas,
    numero_questao,
    tipo_questao,
    pagina_inicial,
    pagina_final,
    arquivo_origem,
):
    """Segmenta uma questao em um intervalo de paginas conhecido."""

    if not 1 <= pagina_inicial <= pagina_final <= len(paginas):
        raise ValueError("Intervalo de paginas invalido.")

    partes = []

    for numero_pagina in range(pagina_inicial, pagina_final + 1):
        texto = limpar_texto_pagina(
            paginas[numero_pagina - 1]["texto"],
            numero_pagina,
        )

        linhas = texto.splitlines()

        titulos = [
            (indice, questao)
            for indice, linha in enumerate(linhas)
            if (questao := identificar_titulo(linha))
        ]

        if numero_pagina == pagina_inicial:
            encontrados = [
                indice
                for indice, questao in titulos
                if questao["numero_questao"] == numero_questao
                and questao["tipo_questao"] == tipo_questao
            ]

            if len(encontrados) != 1 or len(titulos) != 1:
                raise ValueError(
                    "Nao foi possivel isolar o titulo da questao."
                )

            linhas = linhas[encontrados[0] + 1:]

        elif titulos:
            raise ValueError(
                "Outra questao encontrada no intervalo informado."
            )

        partes.append("\n".join(linhas))

    texto_completo = "\n".join(partes)
    resultado = separar_alternativas(texto_completo)

    return {
        "numero_questao": numero_questao,
        "tipo_questao": tipo_questao,
        "texto": resultado["texto"],
        "alternativas": resultado["alternativas"],
        "origem": {
            "arquivo": arquivo_origem,
            "pagina": pagina_inicial,
        },
        "pagina_final": pagina_final,
    }

def eh_pagina_questionario(texto):
    """Identifica o titulo do questionario no inicio da pagina."""

    titulo = "QUESTIONARIO DE PERCEPCAO DA PROVA"

    linhas = [
        " ".join(normalizar_texto(linha).split())
        for linha in texto.splitlines()
        if linha.strip()
    ]

    return titulo in linhas[:5]

def identificar_questoes_em_colunas(texto_pagina, colunas, numero_pagina):
    """Identifica questoes por coluna, ignorando questionarios."""

    if eh_pagina_questionario(texto_pagina):
        return []

    questoes = []

    for nome_coluna in ("esquerda", "direita"):
        texto = limpar_texto_pagina(
            colunas[nome_coluna],
            numero_pagina,
        )

        for linha in texto.splitlines():
            questao = identificar_titulo(linha)

            if questao:
                questoes.append({
                    "numero_questao": questao["numero_questao"],
                    "tipo_questao": questao["tipo_questao"],
                    "pagina": numero_pagina,
                    "coluna": nome_coluna,
                })

    return questoes

def segmentar_questao_em_coluna(
    texto_pagina,
    colunas,
    numero_pagina,
    nome_coluna,
    numero_questao,
    tipo_questao,
    arquivo_origem,
):
    """Segmenta uma questao localizada em uma coluna do PDF."""

    if eh_pagina_questionario(texto_pagina):
        raise ValueError("Pagina do questionario de percepcao.")

    if nome_coluna not in ("esquerda", "direita"):
        raise ValueError("Nome de coluna invalido.")

    texto = limpar_texto_pagina(
        colunas[nome_coluna],
        numero_pagina,
    )

    linhas = texto.splitlines()

    titulos = [
        (indice, questao)
        for indice, linha in enumerate(linhas)
        if (questao := identificar_titulo(linha))
    ]

    encontrados = [
        indice
        for indice, questao in titulos
        if questao["numero_questao"] == numero_questao
        and questao["tipo_questao"] == tipo_questao
    ]

    if len(encontrados) != 1:
        raise ValueError("Questao nao encontrada de forma unica.")

    inicio = encontrados[0]

    fim = next(
        (indice for indice, _ in titulos if indice > inicio),
        len(linhas),
    )

    conteudo = "\n".join(linhas[inicio + 1:fim])
    resultado = separar_alternativas(conteudo)

    return {
        "numero_questao": numero_questao,
        "tipo_questao": tipo_questao,
        "texto": resultado["texto"],
        "alternativas": resultado["alternativas"],
        "origem": {
            "arquivo": arquivo_origem,
            "pagina": numero_pagina,
            "coluna": nome_coluna,
        },
        "pagina_final": numero_pagina,
    }

def segmentar_questoes_na_mesma_pagina(
    texto_pagina,
    numero_pagina,
    arquivo_origem,
):
    """Segmenta questoes delimitadas por titulos na mesma pagina."""

    texto = limpar_texto_pagina(
        texto_pagina,
        numero_pagina,
    )

    linhas = texto.splitlines()

    titulos = [
        (indice, questao)
        for indice, linha in enumerate(linhas)
        if (questao := identificar_titulo(linha))
    ]

    if len(titulos) < 2:
        raise ValueError(
            "A pagina precisa conter pelo menos duas questoes."
        )

    questoes = []

    for posicao, (inicio, identificacao) in enumerate(titulos):
        fim = (
            titulos[posicao + 1][0]
            if posicao + 1 < len(titulos)
            else len(linhas)
        )

        conteudo = "\n".join(linhas[inicio + 1:fim])
        resultado = separar_alternativas(conteudo)

        questoes.append({
            "numero_questao": identificacao["numero_questao"],
            "tipo_questao": identificacao["tipo_questao"],
            "texto": resultado["texto"],
            "alternativas": resultado["alternativas"],
            "origem": {
                "arquivo": arquivo_origem,
                "pagina": numero_pagina,
            },
            "pagina_final": numero_pagina,
        })

    return questoes

def mapear_questoes_prova(paginas, caminho_pdf):
    """Mapeia as questoes e suas localizacoes na prova."""

    questoes = []

    for pagina in paginas:
        numero_pagina = pagina["pagina"]
        texto = pagina["texto"]

        if eh_pagina_questionario(texto):
            continue

        titulos = [
            identificar_titulo(linha)
            for linha in texto.splitlines()
            if identificar_titulo(linha)
        ]

        if titulos:
            for titulo in titulos:
                questoes.append({
                    **titulo,
                    "pagina": numero_pagina,
                    "coluna": None,
                })
            continue

        colunas = extrair_colunas(
            caminho_pdf, numero_pagina
        )["colunas"]

        questoes.extend(
            identificar_questoes_em_colunas(
                texto,
                colunas,
                numero_pagina,
            )
        )

    return questoes