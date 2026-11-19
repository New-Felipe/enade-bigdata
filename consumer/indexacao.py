INDICE_QUESTOES = "enade-questoes"


def indexar_questao(cliente, questao):
    resposta = cliente.index(
        index=INDICE_QUESTOES,
        id=questao["id"],
        document=questao,
    )

    return resposta
