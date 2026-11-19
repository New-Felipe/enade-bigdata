"""Validador do modelo estruturado de questão ENADE (Issue #1).

Executa, nesta ordem:
1. Validação do próprio JSON Schema (Draft 2020-12).
2. Validação estrutural dos exemplos em docs/exemplos/ contra o Schema.
3. Verificações semânticas (regras que comparam campos entre si).
4. Casos de teste positivos e negativos, que conferem a regra esperada.

Uso (a partir de qualquer diretório):
    py scripts/validar_modelo.py
"""

import copy
import json
import re
import sys
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator

RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_SCHEMA = RAIZ / "docs" / "schemas" / "questao.schema.json"
DIRETORIO_EXEMPLOS = RAIZ / "docs" / "exemplos"

CURSO_FORMACAO_GERAL = "Formação Geral"
SIGLA_TIPO_QUESTAO = {"objetiva": "obj", "discursiva": "disc"}
MINIMO_ALTERNATIVAS_OBJETIVA = 2

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# Regras semânticas
# ---------------------------------------------------------------------------

def normalizar_slug(texto):
    """Minúsculas, sem acentos, palavras separadas por hífen."""
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_acentos = "".join(c for c in decomposto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sem_acentos.lower()).strip("-")


def gerar_id(doc):
    """Gera o id esperado: enade-{curso_slug}-{ano}-{tipo_conteudo}-{tipo_questao}-q{numero}.

    Retorna None quando os campos necessários ainda não são válidos; nesse caso
    o problema é reportado pela validação estrutural.
    """
    curso = doc.get("curso")
    ano = doc.get("ano")
    numero = doc.get("numero_questao")
    tipo_conteudo = doc.get("tipo_conteudo")
    tipo_questao = doc.get("tipo_questao")

    if not isinstance(curso, str) or not normalizar_slug(curso):
        return None
    if type(ano) is not int or type(numero) is not int or numero < 1:
        return None
    if tipo_conteudo not in ("FG", "CE"):
        return None
    if not isinstance(tipo_questao, str) or tipo_questao not in SIGLA_TIPO_QUESTAO:
        return None

    return (
        f"enade-{normalizar_slug(curso)}-{ano}-{tipo_conteudo.lower()}-"
        f"{SIGLA_TIPO_QUESTAO[tipo_questao]}-q{numero:02d}"
    )


def verificar_semantica(doc):
    """Retorna a lista de violações das regras que comparam campos entre si."""
    erros = []

    if not isinstance(doc, dict):
        return erros

    # Correspondência entre o id e os metadados.
    esperado = gerar_id(doc)
    encontrado = doc.get("id")
    if esperado is not None and isinstance(encontrado, str) and encontrado != esperado:
        erros.append(
            "[semântica] id incompatível com os campos do documento: "
            f"encontrado '{encontrado}', esperado '{esperado}'."
        )

    # Formação Geral é cadastrada uma única vez, com curso "Formação Geral".
    tipo_conteudo = doc.get("tipo_conteudo")
    curso = doc.get("curso")
    if isinstance(curso, str):
        if tipo_conteudo == "FG" and curso != CURSO_FORMACAO_GERAL:
            erros.append(
                "[semântica] questão de Formação Geral (FG) deve usar "
                f"curso '{CURSO_FORMACAO_GERAL}'."
            )
        if tipo_conteudo == "CE" and curso == CURSO_FORMACAO_GERAL:
            erros.append(
                "[semântica] questão de Componente Específico (CE) deve usar "
                f"o nome do curso, não '{CURSO_FORMACAO_GERAL}'."
            )

    # Alternativas: letras únicas.
    alternativas = doc.get("alternativas")
    quantidade = len(alternativas) if isinstance(alternativas, list) else None
    letras = []
    if quantidade is not None:
        letras = [
            a["letra"]
            for a in alternativas
            if isinstance(a, dict) and isinstance(a.get("letra"), str)
        ]
        duplicadas = sorted({letra for letra in letras if letras.count(letra) > 1})
        if duplicadas:
            erros.append(
                "[semântica] letra(s) de alternativa duplicada(s): "
                f"{', '.join(duplicadas)}."
            )

    gabarito = doc.get("gabarito")
    tipo_questao = doc.get("tipo_questao")

    if tipo_questao == "objetiva":
        if quantidade is not None and quantidade < MINIMO_ALTERNATIVAS_OBJETIVA:
            erros.append(
                "[semântica] questão objetiva exige pelo menos "
                f"{MINIMO_ALTERNATIVAS_OBJETIVA} alternativas (encontradas: {quantidade})."
            )
        if isinstance(gabarito, str) and gabarito not in letras:
            erros.append(
                f"[semântica] gabarito '{gabarito}' não corresponde a nenhuma "
                f"alternativa cadastrada (letras existentes: {', '.join(letras) or 'nenhuma'})."
            )
        if doc.get("anulada") is True and gabarito is not None:
            erros.append("[semântica] questão objetiva anulada deve ter gabarito null.")

    elif tipo_questao == "discursiva":
        if quantidade:
            erros.append("[semântica] questão discursiva não pode ter alternativas.")
        if gabarito is not None:
            erros.append("[semântica] questão discursiva deve ter gabarito null.")

    return erros


def validar_documento(validador, doc):
    """Valida um documento (Schema + semântica). Retorna a lista de erros."""
    erros_schema = sorted(
        validador.iter_errors(doc),
        key=lambda erro: [str(parte) for parte in erro.absolute_path],
    )
    erros = [
        f"[schema] {'.'.join(str(p) for p in erro.absolute_path) or '(raiz)'}: {erro.message}"
        for erro in erros_schema
    ]
    return erros + verificar_semantica(doc)


# ---------------------------------------------------------------------------
# Casos de teste
# ---------------------------------------------------------------------------

def variar(base, **campos):
    """Cópia profunda do documento base com os campos alterados."""
    doc = copy.deepcopy(base)
    doc.update(campos)
    return doc


def alternativas_de(letras):
    return [{"letra": l, "texto": f"Texto da alternativa {l}."} for l in letras]


def montar_casos(objetiva, discursiva):
    """Retorna [(nome, documento, esperado)].

    esperado=None: o documento deve ser aceito.
    esperado=[fragmentos]: o documento deve ser rejeitado; cada fragmento deve
    aparecer em alguma mensagem e TODA mensagem deve conter algum fragmento,
    ou seja, a rejeição ocorre exatamente pela regra esperada.
    """
    casos = []

    def aceita(nome, doc):
        casos.append((nome, doc, None))

    def rejeita(nome, doc, *fragmentos):
        casos.append((nome, doc, list(fragmentos)))

    # Fixtures de Formação Geral (valores fictícios, apenas para teste).
    fg_obj = variar(
        objetiva,
        id="enade-formacao-geral-2023-fg-obj-q01",
        curso=CURSO_FORMACAO_GERAL,
        tipo_conteudo="FG",
        area=CURSO_FORMACAO_GERAL,
    )
    fg_disc = variar(
        discursiva,
        id="enade-formacao-geral-2023-fg-disc-q01",
        curso=CURSO_FORMACAO_GERAL,
        tipo_conteudo="FG",
        area=CURSO_FORMACAO_GERAL,
        numero_questao=1,
    )

    # ----- Positivos -----
    aceita("P1 objetiva: gabarito corresponde a uma alternativa (B)", objetiva)
    aceita("P1b objetiva: gabarito corresponde a uma alternativa (E)", variar(objetiva, gabarito="E"))
    aceita("P2 objetiva não anulada com gabarito null (indisponível)", variar(objetiva, gabarito=None))
    aceita("P3 discursiva com alternativas [] e gabarito null", discursiva)
    aceita(
        "P4 objetiva anulada, alternativas preservadas, gabarito null",
        variar(objetiva, anulada=True, gabarito=None),
    )
    aceita("P5 Formação Geral objetiva (curso 'Formação Geral', FG)", fg_obj)
    aceita("P5b Formação Geral discursiva (curso 'Formação Geral', FG)", fg_disc)
    aceita("P6 discursiva anulada, [] e gabarito null", variar(discursiva, anulada=True))
    aceita(
        "P7 objetiva com exatamente 2 alternativas (mínimo)",
        variar(objetiva, alternativas=alternativas_de("AB"), gabarito="A"),
    )
    aceita(
        "P8 objetiva sem texto_base (campo opcional)",
        {k: v for k, v in objetiva.items() if k != "texto_base"},
    )

    # ----- Negativos: alternativas e gabarito -----
    rejeita(
        "N1 objetiva com apenas uma alternativa",
        variar(objetiva, alternativas=alternativas_de("A"), gabarito="A"),
        "[schema] alternativas:",
        "questão objetiva exige pelo menos 2 alternativas",
    )
    rejeita(
        "N1b objetiva com lista de alternativas vazia",
        variar(objetiva, alternativas=[], gabarito=None),
        "[schema] alternativas:",
        "questão objetiva exige pelo menos 2 alternativas",
    )
    rejeita(
        "N1c objetiva anulada sem alternativas (devem ser preservadas)",
        variar(objetiva, alternativas=[], anulada=True, gabarito=None),
        "[schema] alternativas:",
        "questão objetiva exige pelo menos 2 alternativas",
    )
    rejeita(
        "N2 gabarito 'Z' com alternativas A-E",
        variar(objetiva, gabarito="Z"),
        "não corresponde a nenhuma alternativa cadastrada",
    )
    rejeita(
        "N2b gabarito 'E' com alternativas A-C",
        variar(objetiva, alternativas=alternativas_de("ABC"), gabarito="E"),
        "não corresponde a nenhuma alternativa cadastrada",
    )
    rejeita(
        "N2c gabarito minúsculo 'b'",
        variar(objetiva, gabarito="b"),
        "[schema] gabarito:",
        "não corresponde a nenhuma alternativa cadastrada",
    )

    duplicadas = copy.deepcopy(objetiva["alternativas"])
    duplicadas[1]["letra"] = "A"  # textos continuam diferentes
    rejeita(
        "N3 letras duplicadas (A, A) com textos diferentes",
        variar(objetiva, alternativas=duplicadas, gabarito="A"),
        "letra(s) de alternativa duplicada(s): A",
    )
    rejeita(
        "N3b segunda alternativa alterada para A, gabarito B mantido",
        variar(objetiva, alternativas=duplicadas),
        "letra(s) de alternativa duplicada(s): A",
        "não corresponde a nenhuma alternativa cadastrada",
    )

    fora_do_conjunto = copy.deepcopy(objetiva["alternativas"])
    fora_do_conjunto[4]["letra"] = "F"
    rejeita(
        "N3c letra de alternativa fora de A-E (F)",
        variar(objetiva, alternativas=fora_do_conjunto),
        "[schema] alternativas.4.letra:",
    )

    texto_vazio = copy.deepcopy(objetiva["alternativas"])
    texto_vazio[1]["texto"] = ""
    rejeita(
        "N4 texto de alternativa vazio",
        variar(objetiva, alternativas=texto_vazio),
        "[schema] alternativas.1.texto:",
    )
    texto_espacos = copy.deepcopy(objetiva["alternativas"])
    texto_espacos[1]["texto"] = "   "
    rejeita(
        "N5 texto de alternativa somente com espaços",
        variar(objetiva, alternativas=texto_espacos),
        "[schema] alternativas.1.texto: '   ' does not match",
    )

    # ----- Negativos: anulação e discursivas -----
    rejeita(
        "N6 objetiva anulada com gabarito preenchido",
        variar(objetiva, anulada=True),
        "[schema] gabarito:",
        "questão objetiva anulada deve ter gabarito null",
    )
    rejeita(
        "N7 discursiva com alternativas",
        variar(discursiva, alternativas=alternativas_de("A")),
        "[schema] alternativas:",
        "questão discursiva não pode ter alternativas",
    )
    rejeita(
        "N8 discursiva com gabarito preenchido",
        variar(discursiva, gabarito="A"),
        "[schema] gabarito:",
        "questão discursiva deve ter gabarito null",
    )

    # ----- Negativos: id incompatível com os metadados -----
    rejeita(
        "N9a id com curso diferente do campo curso",
        variar(objetiva, id="enade-engenharia-de-computacao-2023-ce-obj-q01"),
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9b id com ano diferente do campo ano",
        variar(objetiva, id="enade-sistemas-de-informacao-2022-ce-obj-q01"),
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9c id com tipo de conteúdo diferente (fg x CE)",
        variar(objetiva, id="enade-sistemas-de-informacao-2023-fg-obj-q01"),
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9d id com tipo de questão diferente (disc x objetiva)",
        variar(objetiva, id="enade-sistemas-de-informacao-2023-ce-disc-q01"),
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9e id com número diferente do campo numero_questao",
        variar(objetiva, id="enade-sistemas-de-informacao-2023-ce-obj-q02"),
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9f campo ano alterado, id mantido",
        variar(objetiva, ano=2022),
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9g campo numero_questao alterado, id mantido",
        variar(objetiva, numero_questao=2),
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9h campo curso alterado, id mantido",
        variar(objetiva, curso="Engenharia de Computação"),
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9i id sem zero à esquerda no número (q1)",
        variar(objetiva, id="enade-sistemas-de-informacao-2023-ce-obj-q1"),
        "[schema] id:",
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9j id no padrão antigo (sem tipo de questão)",
        variar(objetiva, id="enade-si-2023-ce-q01"),
        "[schema] id:",
        "id incompatível com os campos do documento",
    )
    rejeita(
        "N9k FG com curso diferente de 'Formação Geral'",
        variar(fg_obj, curso="Sistemas de Informação", id="enade-sistemas-de-informacao-2023-fg-obj-q01"),
        "deve usar curso 'Formação Geral'",
    )
    rejeita(
        "N9l CE com curso 'Formação Geral'",
        variar(fg_obj, tipo_conteudo="CE", id="enade-formacao-geral-2023-ce-obj-q01"),
        "deve usar o nome do curso, não 'Formação Geral'",
    )

    # ----- Negativos: enums -----
    rejeita(
        "N10 tipo_questao inválido",
        variar(objetiva, tipo_questao="mista"),
        "[schema] tipo_questao:",
    )
    rejeita(
        "N11 tipo_conteudo inválido",
        variar(objetiva, tipo_conteudo="XX"),
        "[schema] tipo_conteudo:",
    )

    # ----- Negativos: textos somente com espaços -----
    rejeita("N12a enunciado somente com espaços", variar(objetiva, enunciado="   "), "[schema] enunciado:")
    rejeita("N12b enunciado vazio", variar(objetiva, enunciado=""), "[schema] enunciado:")
    rejeita("N12c texto_base somente com espaços", variar(objetiva, texto_base=" \n\t "), "[schema] texto_base:")
    rejeita("N12d area somente com espaços", variar(objetiva, area="   "), "[schema] area:")
    rejeita("N12e curso somente com espaços", variar(objetiva, curso="   "), "[schema] curso:")
    rejeita(
        "N12f origem.arquivo somente com espaços",
        variar(objetiva, origem={"arquivo": "   ", "pagina": 5}),
        "[schema] origem.arquivo:",
    )
    rejeita(
        "N12g objeto de conhecimento somente com espaços",
        variar(objetiva, objetos_conhecimento=["   "]),
        "[schema] objetos_conhecimento.0:",
    )
    rejeita(
        "N12h competência somente com espaços",
        variar(objetiva, competencias=["   "]),
        "[schema] competencias.0:",
    )

    # ----- Negativos: estrutura -----
    sem_gabarito = copy.deepcopy(objetiva)
    del sem_gabarito["gabarito"]
    rejeita(
        "N13 campo gabarito ausente (obrigatório, aceita null)",
        sem_gabarito,
        "'gabarito' is a required property",
    )
    rejeita(
        "N14 propriedade não documentada",
        variar(objetiva, schema_version="1.0"),
        "Additional properties are not allowed",
    )

    return casos


def executar_caso(validador, nome, doc, esperado):
    """Retorna (aprovado, detalhe)."""
    erros = validar_documento(validador, doc)

    if esperado is None:
        if erros:
            return False, "esperava aceitar, mas foi rejeitado:\n      " + "\n      ".join(erros)
        return True, "aceito"

    if not erros:
        return False, "esperava rejeitar, mas o documento foi aceito"

    ausentes = [f for f in esperado if not any(f in e for e in erros)]
    inesperados = [e for e in erros if not any(f in e for f in esperado)]
    if ausentes or inesperados:
        detalhe = "rejeitado, porém por regra diferente da esperada:"
        for f in ausentes:
            detalhe += f"\n      regra esperada não disparou: {f!r}"
        for e in inesperados:
            detalhe += f"\n      erro inesperado: {e}"
        return False, detalhe
    return True, "rejeitado pela regra esperada"


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

def main():
    falhas = 0

    # 1. Carrega o JSON Schema.
    schema = json.loads(CAMINHO_SCHEMA.read_text(encoding="utf-8"))

    # 2. Verifica se o próprio Schema está correto.
    Draft202012Validator.check_schema(schema)
    print("OK: JSON Schema válido (Draft 2020-12).")
    validador = Draft202012Validator(schema)

    # 3. Localiza os exemplos de questões.
    arquivos = sorted(DIRETORIO_EXEMPLOS.glob("questao-*.json"))
    if not arquivos:
        raise SystemExit("Nenhum exemplo encontrado.")

    # 4/5. Valida cada exemplo (Schema + semântica).
    documentos = {}
    ids_vistos = {}
    print("\nExemplos:")
    for arquivo in arquivos:
        documento = json.loads(arquivo.read_text(encoding="utf-8"))
        documentos[arquivo.name] = documento
        erros = validar_documento(validador, documento)

        if erros:
            falhas += 1
            print(f"ERRO: {arquivo.relative_to(RAIZ)}")
            for erro in erros:
                print(f"  - {erro}")
        else:
            print(f"OK: {arquivo.relative_to(RAIZ)}")

        identificador = documento.get("id")
        if identificador in ids_vistos:
            falhas += 1
            print(f"ERRO: id repetido entre exemplos: {identificador}")
        ids_vistos[identificador] = arquivo.name

    # 6. Testes positivos e negativos.
    objetiva = documentos.get("questao-objetiva.json")
    discursiva = documentos.get("questao-discursiva.json")
    if objetiva is None or discursiva is None:
        raise SystemExit("Exemplos questao-objetiva.json e questao-discursiva.json são obrigatórios.")

    print("\nTestes de documentos:")
    total = 0
    for nome, doc, esperado in montar_casos(objetiva, discursiva):
        total += 1
        aprovado, detalhe = executar_caso(validador, nome, doc, esperado)
        if aprovado:
            print(f"OK:    {nome} -> {detalhe}")
        else:
            falhas += 1
            print(f"FALHA: {nome} -> {detalhe}")

    # Verificações da geração do id.
    print("\nTestes de geração de id:")
    verificacoes = [
        (
            "normalizar 'Sistemas de Informação' -> 'sistemas-de-informacao'",
            normalizar_slug("Sistemas de Informação") == "sistemas-de-informacao",
        ),
        (
            "normalizar 'Formação Geral' -> 'formacao-geral'",
            normalizar_slug("Formação Geral") == "formacao-geral",
        ),
        (
            "id do exemplo objetivo é o gerado pelos campos",
            gerar_id(objetiva) == "enade-sistemas-de-informacao-2023-ce-obj-q01",
        ),
        (
            "id distingue objetiva e discursiva com mesmo curso, ano e número",
            gerar_id(variar(discursiva, numero_questao=1))
            != gerar_id(variar(objetiva, numero_questao=1)),
        ),
        (
            "id é determinístico (mesma entrada, mesmo id)",
            gerar_id(objetiva) == gerar_id(copy.deepcopy(objetiva)),
        ),
    ]
    for nome, aprovado in verificacoes:
        total += 1
        if aprovado:
            print(f"OK:    {nome}")
        else:
            falhas += 1
            print(f"FALHA: {nome}")

    print()
    if falhas:
        print(f"{falhas} falha(s) encontrada(s) em {total} teste(s) e nos exemplos.")
        raise SystemExit(1)

    print(f"Todos os testes foram concluídos com sucesso! ({total} testes + {len(arquivos)} exemplos)")


if __name__ == "__main__":
    main()
