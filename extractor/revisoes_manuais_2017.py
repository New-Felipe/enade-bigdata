"""Revisoes verificadas de questoes do ENADE 2017."""
from copy import deepcopy
ARQUIVO_PROVA_2017 = (
    "enade_2017_sistemas_de_informacao_prova.pdf"
)
REVISOES = {
    ("objetiva", 14): {
        "pagina": 21,
        "arquivo": ARQUIVO_PROVA_2017,
        "alternativas": {
            "A": "I, apenas.",
            "B": "I e III, apenas.",
            "C": "II e IV, apenas.",
            "D": "II, III e IV, apenas.",
            "E": "I, II, III e IV.",
        },
    },
}
def revisar_alternativas_2017(questao):
    """Aplica somente correcoes conferidas na prova original."""

    if (
        questao.get("tipo_questao") == "objetiva"
        and questao.get("numero_questao") == 15
        and (questao.get("origem") or {}).get("arquivo")
        == "enade_2017_sistemas_de_informacao_prova.pdf"
        and (questao.get("origem") or {}).get("pagina") == 22
    ):
        return _revisar_alternativas_questao_15(questao)
    recuperada = deepcopy(questao)
    chave = (
        recuperada["tipo_questao"],
        recuperada["numero_questao"],
    )
    revisao = REVISOES.get(chave)
    if revisao is None:
        return recuperada
    origem = recuperada["origem"]
    if (
        origem.get("pagina") != revisao["pagina"]
        or origem.get("arquivo") != revisao["arquivo"]
    ):
        raise ValueError(
            "Origem da questao nao corresponde "
            "a revisao manual verificada."
        )
    alternativas = recuperada["alternativas"]
    letras = [
        alternativa["letra"]
        for alternativa in alternativas
    ]
    if letras != list("ABCDE"):
        raise ValueError(
            "Revisao manual exige alternativas A-E "
            "na ordem correta."
        )
    # Preserva os resultados do OCR para auditoria.
    alternativas_ocr = deepcopy(alternativas)
    for alternativa in alternativas:
        letra = alternativa["letra"]
        alternativa["texto"] = revisao["alternativas"][letra]
    recuperada["revisao_manual"] = {
        "pagina": revisao["pagina"],
        "arquivo": revisao["arquivo"],
        "motivo": (
            "Algarismos romanos conferidos visualmente "
            "na imagem da prova oficial."
        ),
        "alternativas_ocr": alternativas_ocr,
    }
    return recuperada

def revisar_enunciado_2017(questao):
    """Corrige marcadores romanos verificados na prova oficial."""

    if (
        questao.get("tipo_questao") == "objetiva"
        and questao.get("numero_questao") == 15
        and (questao.get("origem") or {}).get("arquivo")
        == "enade_2017_sistemas_de_informacao_prova.pdf"
        and (questao.get("origem") or {}).get("pagina") == 22
    ):
        return _revisar_enunciado_questao_15(questao)
    import re
    recuperada = deepcopy(questao)
    chave = (
        recuperada["tipo_questao"],
        recuperada["numero_questao"],
    )
    # Somente questoes com revisao previamente verificada.
    revisao = REVISOES.get(chave)
    if revisao is None:
        return recuperada
    origem = recuperada["origem"]
    if (
        origem.get("arquivo") != revisao["arquivo"]
        or origem.get("pagina") != revisao["pagina"]
    ):
        raise ValueError(
            "Origem da questao nao corresponde "
            "a revisao manual verificada."
        )
    # Atualmente a revisao de enunciado foi conferida
    # visualmente apenas para a questao objetiva 14.
    if chave != ("objetiva", 14):
        return recuperada
    texto_original = recuperada["texto"]
    equivalencias = {
        "|": "I",
        "I": "I",
        "Il": "II",
        "II": "II",
        "Ill": "III",
        "III": "III",
        "IV": "IV",
    }
    # Reconhece marcadores apenas no inicio das linhas.
    # Nao altera simbolos encontrados dentro das frases.
    padrao = re.compile(
        r"(?m)^(?P<recuo>[ \t]*)"
        r"(?P<marcador>\||Ill|III|Il|II|IV|I)"
        r"\.(?P<espaco>[ \t]+)"
    )
    encontrados = list(padrao.finditer(texto_original))
    marcadores = [
        equivalencias[item.group("marcador")]
        for item in encontrados
    ]
    if marcadores != ["I", "II", "III", "IV"]:
        raise ValueError(
            "Nao foi possivel confirmar a sequencia "
            "das quatro afirmacoes."
        )
    def substituir(correspondencia):
        marcador = correspondencia.group("marcador")
        correto = equivalencias[marcador]
        return (
            correspondencia.group("recuo")
            + correto
            + "."
            + correspondencia.group("espaco")
        )
    # Remove o Z isolado, conferido visualmente na prova.
    # A regra exige uma linha exclusiva seguida de linha vazia.
    texto_sem_artefato = re.sub(
        r"(?m)^[ \t]*Z[ \t]*\n[ \t]*\n",
        "",
        texto_original,
    )
    texto_revisado = padrao.sub(
        substituir,
        texto_sem_artefato,
    )
    recuperada["texto"] = texto_revisado
    # Mantem as informacoes de revisoes anteriores.
    registro = recuperada.setdefault(
        "revisao_manual",
        {},
    )
    registro["texto_ocr"] = texto_original
    registro["motivo_enunciado"] = (
        "Marcadores romanos I-IV conferidos "
        "visualmente na pagina 21 da prova oficial."
    )
    return recuperada

def _validar_origem_questao_15(questao):
    """Confere a origem da revisao visual da questao 15."""
    origem = questao.get("origem") or {}
    if (
        origem.get("arquivo")
        != "enade_2017_sistemas_de_informacao_prova.pdf"
        or origem.get("pagina") != 22
    ):
        raise ValueError(
            "Origem incorreta para a revisao da questao 15."
        )
def _revisar_alternativas_questao_15(questao):
    """Aplica as alternativas conferidas na pagina 22."""
    from copy import deepcopy
    revisada = deepcopy(questao)
    _validar_origem_questao_15(revisada)
    alternativas = revisada.get("alternativas", [])
    if [
        item.get("letra")
        for item in alternativas
    ] != list("ABCDE"):
        raise ValueError(
            "Alternativas A-E incompletas na questao 15."
        )

    # Confere se o OCR corresponde semanticamente
    # as cinco alternativas verificadas na prova.
    # Nao substitui conteudo desconhecido por texto manual.
    import unicodedata
    assinaturas_esperadas = [
        (
            "assercoes",
            "proposicoes verdadeiras",
            "justificativa correta",
        ),
        (
            "assercoes",
            "proposicoes verdadeiras",
            "mas",
            "nao",
            "justificativa correta",
        ),
        (
            "assercao",
            "proposicao verdadeira",
            "proposicao falsa",
        ),
        (
            "assercao",
            "proposicao falsa",
            "proposicao verdadeira",
        ),
        (
            "assercoes",
            "proposicoes falsas",
        ),
    ]
    def normalizar_conteudo(valor):
        if not isinstance(valor, str):
            return ""
        decomposicao = unicodedata.normalize(
            "NFKD",
            valor.lower(),
        )
        return "".join(
            caractere
            for caractere in decomposicao
            if not unicodedata.combining(caractere)
        )
    textos_ocr = [
        normalizar_conteudo(item.get("texto"))
        for item in alternativas
    ]
    compativeis = all(
        all(
            assinatura in texto
            for assinatura in assinaturas
        )
        for texto, assinaturas in zip(
            textos_ocr,
            assinaturas_esperadas,
        )
    )
    if not compativeis:
        # Preserva o OCR sem aplicar substituicoes
        # que nao podem ser justificadas pelo conteudo.
        return revisada
    esperadas = [
        (
            "As asser\u00e7\u00f5es I e II s\u00e3o proposi\u00e7\u00f5es "
            "verdadeiras, e a II \u00e9 uma justificativa "
            "correta de I."
        ),
        (
            "As asser\u00e7\u00f5es I e II s\u00e3o proposi\u00e7\u00f5es "
            "verdadeiras, mas a II n\u00e3o \u00e9 uma "
            "justificativa correta de I."
        ),
        (
            "A asser\u00e7\u00e3o I \u00e9 uma proposi\u00e7\u00e3o "
            "verdadeira, e a II \u00e9 uma proposi\u00e7\u00e3o "
            "falsa."
        ),
        (
            "A asser\u00e7\u00e3o I \u00e9 uma proposi\u00e7\u00e3o "
            "falsa, e a II \u00e9 uma proposi\u00e7\u00e3o "
            "verdadeira."
        ),
        (
            "As asser\u00e7\u00f5es I e II s\u00e3o "
            "proposi\u00e7\u00f5es falsas."
        ),
    ]
    registro = revisada.setdefault("revisao_manual", {})
    registro["alternativas_ocr"] = deepcopy(alternativas)
    registro["motivo_alternativas"] = (
        "Algarismos romanos conferidos visualmente "
        "na pagina 22 da prova oficial."
    )
    for alternativa, texto in zip(
        revisada["alternativas"],
        esperadas,
    ):
        alternativa["texto"] = texto
    return revisada
def _revisar_enunciado_questao_15(questao):
    """Corrige as assercoes I e II da questao 15."""
    from copy import deepcopy
    import re
    revisada = deepcopy(questao)
    _validar_origem_questao_15(revisada)
    original = revisada["texto"]
    padrao_i = re.compile(
        r"(?m)^[ \t]*(?:\||I)\.?[ \t]+"
        r"(?=A abordagem ASI\b)"
    )
    padrao_ii = re.compile(
        r"(?m)^[ \t]*(?:Il|II|ll)\.[ \t]+"
        r"(?=O objetivo da ASI\b)"
    )
    if (
        len(padrao_i.findall(original)) != 1
        or len(padrao_ii.findall(original)) != 1
    ):
        raise ValueError(
            "Nao foi possivel confirmar os marcadores "
            "das duas assercoes."
        )
    texto = padrao_i.sub("I. ", original, count=1)
    texto = padrao_ii.sub("II. ", texto, count=1)
    revisada["texto"] = texto
    registro = revisada.setdefault("revisao_manual", {})
    registro["texto_ocr"] = original
    registro["motivo_enunciado"] = (
        "Marcadores I e II conferidos visualmente "
        "na pagina 22 da prova oficial."
    )
    return revisada
