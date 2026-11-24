"""Conversao de questoes extraidas para o modelo canonico ENADE."""

from extractor.classificacao import classificar_tipo_conteudo
from scripts.validar_modelo import gerar_id


def converter_questao_canonica(questao, ano):
    """Converte uma questao com gabarito associado ao modelo canonico."""

    tipo_conteudo = classificar_tipo_conteudo(questao, ano)

    if tipo_conteudo == "FG":
        curso = "Formação Geral"
        area = "Formação Geral"
    else:
        curso = "Sistemas de Informação"
        area = "Computação"

    documento = {
        "area": area,
        "curso": curso,
        "ano": ano,
        "numero_questao": questao["numero_questao"],
        "tipo_conteudo": tipo_conteudo,
        "tipo_questao": questao["tipo_questao"],
        "enunciado": questao["texto"].strip(),
        "alternativas": [
            {
                "letra": alternativa["letra"],
                "texto": alternativa["texto"],
            }
            for alternativa in questao["alternativas"]
        ],
        "gabarito": questao["gabarito"],
        "anulada": questao["anulada"],
        "objetos_conhecimento": [],
        "competencias": [],
        "origem": {
            "arquivo": questao["origem"]["arquivo"],
            "pagina": questao["origem"]["pagina"],
        },
    }

    documento["id"] = gerar_id(documento)

    return documento
