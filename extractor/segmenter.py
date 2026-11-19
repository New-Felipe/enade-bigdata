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

def eh_pagina_apenas_rascunho(texto):
    """Identifica paginas compostas somente por rascunho e marcadores."""
    linhas = [
        normalizar_texto(linha).strip().upper()
        for linha in texto.splitlines()
        if linha.strip()
    ]

    if "RASCUNHO" not in linhas or "AREA LIVRE" not in linhas:
        return False

    marcadores = {
        "RASCUNHO",
        "AREA LIVRE",
        "SISTEMAS DE INFORMACAO",
    }

    return all(
        linha in marcadores or linha.isdecimal()
        for linha in linhas
    )

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

    # Desconsidera paginas finais compostas apenas por rascunho.
    while pagina_final > pagina_inicial:
        texto_final = limpar_texto_pagina(
            paginas[pagina_final - 1]["texto"],
            pagina_final,
        )

        if not eh_pagina_apenas_rascunho(texto_final):
            break

        pagina_final -= 1

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

def planejar_extracao_questoes(questoes, ultima_pagina):
    """Calcula intervalos candidatos para a extracao das questoes."""

    planos = []

    for indice, questao in enumerate(questoes):
        pagina_inicial = questao["pagina"]

        if indice + 1 < len(questoes):
            proxima = questoes[indice + 1]

            if proxima["pagina"] == pagina_inicial:
                pagina_final = pagina_inicial
            else:
                pagina_final = proxima["pagina"] - 1
        else:
            pagina_final = ultima_pagina - 1

        planos.append({
            **questao,
            "pagina_inicial": pagina_inicial,
            "pagina_final_candidata": pagina_final,
            "multiplas_paginas": pagina_final > pagina_inicial,
        })

    return planos

def extrair_questoes_pagina_unica(paginas, planos, arquivo_origem):
    """Extrai questoes que ocupam sozinhas uma unica pagina."""

    questoes_extraidas = []
    pendentes = []

    quantidade_por_pagina = {}

    for plano in planos:
        pagina = plano["pagina_inicial"]
        quantidade_por_pagina[pagina] = (
            quantidade_por_pagina.get(pagina, 0) + 1
        )

    for plano in planos:
        pagina = plano["pagina_inicial"]

        if (
            plano["multiplas_paginas"]
            or quantidade_por_pagina[pagina] != 1
        ):
            pendentes.append(plano)
            continue

        try:
            questao = segmentar_questao_em_paginas(
                paginas=paginas,
                numero_questao=plano["numero_questao"],
                tipo_questao=plano["tipo_questao"],
                pagina_inicial=pagina,
                pagina_final=pagina,
                arquivo_origem=arquivo_origem,
            )

            questoes_extraidas.append(questao)

        except ValueError:
            pendentes.append(plano)

    return {
        "extraidas": questoes_extraidas,
        "pendentes": pendentes,
    }

def segmentar_questao_com_continuacao(
    paginas,
    numero_questao,
    tipo_questao,
    pagina_inicial,
    pagina_continuacao,
    proxima_questao,
    arquivo_origem,
):
    """Segmenta uma questao que termina antes de outra na pagina seguinte."""

    if not (
        1 <= pagina_inicial < pagina_continuacao <= len(paginas)
        and pagina_continuacao == pagina_inicial + 1
    ):
        raise ValueError("Intervalo de paginas invalido.")

    texto_inicio = limpar_texto_pagina(
        paginas[pagina_inicial - 1]["texto"],
        pagina_inicial,
    )

    texto_continuacao = limpar_texto_pagina(
        paginas[pagina_continuacao - 1]["texto"],
        pagina_continuacao,
    )

    linhas_inicio = texto_inicio.splitlines()
    linhas_continuacao = texto_continuacao.splitlines()

    titulos_inicio = [
        i for i, linha in enumerate(linhas_inicio)
        if (q := identificar_titulo(linha))
        and q["numero_questao"] == numero_questao
        and q["tipo_questao"] == tipo_questao
    ]

    titulos_fim = [
        i for i, linha in enumerate(linhas_continuacao)
        if (q := identificar_titulo(linha))
        and q["numero_questao"] == proxima_questao
        and q["tipo_questao"] == tipo_questao
    ]

    if len(titulos_inicio) != 1 or len(titulos_fim) != 1:
        raise ValueError("Titulos nao encontrados de forma unica.")

    inicio = titulos_inicio[0]
    fim = titulos_fim[0]

    texto_completo = (
        "\n".join(linhas_inicio[inicio + 1:])
        + "\n"
        + "\n".join(linhas_continuacao[:fim])
    )

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
        "pagina_final": pagina_continuacao,
    }


def extrair_questoes_planejadas(
    paginas,
    planos,
    caminho_pdf,
    arquivo_origem,
    continuacoes=None,
):
    """Integra os metodos de extracao conforme o mapeamento."""

    continuacoes = continuacoes or {}
    extraidas = []
    falhas = []

    colunas_cache = {}
    paginas_multiplas_cache = {}

    quantidade_por_pagina = {}

    for plano in planos:
        pagina = plano["pagina_inicial"]
        quantidade_por_pagina[pagina] = (
            quantidade_por_pagina.get(pagina, 0) + 1
        )

    for plano in planos:
        numero = plano["numero_questao"]
        tipo = plano["tipo_questao"]
        pagina = plano["pagina_inicial"]
        chave = (tipo, numero)

        try:
            if chave in continuacoes:
                pagina_final, proxima_questao = continuacoes[chave]

                questao = segmentar_questao_com_continuacao(
                    paginas=paginas,
                    numero_questao=numero,
                    tipo_questao=tipo,
                    pagina_inicial=pagina,
                    pagina_continuacao=pagina_final,
                    proxima_questao=proxima_questao,
                    arquivo_origem=arquivo_origem,
                )

            elif plano.get("coluna"):
                if pagina not in colunas_cache:
                    colunas_cache[pagina] = extrair_colunas(
                        caminho_pdf, pagina
                    )["colunas"]

                questao = segmentar_questao_em_coluna(
                    texto_pagina=paginas[pagina - 1]["texto"],
                    colunas=colunas_cache[pagina],
                    numero_pagina=pagina,
                    nome_coluna=plano["coluna"],
                    numero_questao=numero,
                    tipo_questao=tipo,
                    arquivo_origem=arquivo_origem,
                )

            elif quantidade_por_pagina[pagina] > 1:
                if pagina not in paginas_multiplas_cache:
                    paginas_multiplas_cache[pagina] = (
                        segmentar_questoes_na_mesma_pagina(
                            texto_pagina=paginas[pagina - 1]["texto"],
                            numero_pagina=pagina,
                            arquivo_origem=arquivo_origem,
                        )
                    )

                questao = next(
                    (
                        q for q in paginas_multiplas_cache[pagina]
                        if q["numero_questao"] == numero
                        and q["tipo_questao"] == tipo
                    ),
                    None,
                )

                if questao is None:
                    raise ValueError("Questao nao encontrada.")

            else:
                questao = segmentar_questao_em_paginas(
                    paginas=paginas,
                    numero_questao=numero,
                    tipo_questao=tipo,
                    pagina_inicial=pagina,
                    pagina_final=plano["pagina_final_candidata"],
                    arquivo_origem=arquivo_origem,
                )

            extraidas.append(questao)

        except ValueError as erro:
            falhas.append({
                "tipo_questao": tipo,
                "numero_questao": numero,
                "erro": str(erro),
            })

    revisar = [
        {
            "tipo_questao": q["tipo_questao"],
            "numero_questao": q["numero_questao"],
            "motivo": "Alternativas A-E nao identificadas",
        }
        for q in extraidas
        if q["tipo_questao"] == "objetiva"
        and len(q["alternativas"]) != 5
    ]

    return {
        "extraidas": extraidas,
        "falhas": falhas,
        "revisar": revisar,
    }
