from consumer.indexacao import INDICE_QUESTOES


def buscar_questoes(
    cliente,
    termo,
    tamanho=10,
    ano=None,
    curso=None,
    tipo_questao=None,
):
    filtros = []

    if ano is not None:
        filtros.append({"term": {"ano": ano}})

    if curso is not None:
        filtros.append({"term": {"curso": curso}})

    if tipo_questao is not None:
        filtros.append({"term": {"tipo_questao": tipo_questao}})

    consulta = {
        "match": {
            "enunciado": termo,
        }
    }

    if filtros:
        consulta = {
            "bool": {
                "must": [consulta],
                "filter": filtros,
            }
        }

    return cliente.search(
        index=INDICE_QUESTOES,
        query=consulta,
        highlight={
            "fields": {
                "enunciado": {},
            }
        },
        size=tamanho,
    )


def agregar_questoes(cliente):
    return cliente.search(
        index=INDICE_QUESTOES,
        size=0,
        aggs={
            "por_ano": {
                "terms": {
                    "field": "ano",
                }
            },
            "por_curso": {
                "terms": {
                    "field": "curso",
                }
            },
            "por_tipo": {
                "terms": {
                    "field": "tipo_questao",
                }
            },
        },
    )