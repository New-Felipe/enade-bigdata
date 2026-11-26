"""Classificacao das questoes ENADE por componente da prova."""


def classificar_tipo_conteudo(questao, ano):
    """Identifica FG ou CE nas provas ENADE 2017 e 2021."""

    if ano not in (2017, 2021):
        raise ValueError(
            f"Classificacao nao configurada para o ano {ano}."
        )

    tipo = questao.get("tipo_questao")
    numero = questao.get("numero_questao")

    intervalos = {
        "objetiva": [
            (1, 8, "FG"),
            (9, 35, "CE"),
        ],
        "discursiva": [
            (1, 2, "FG"),
            (3, 5, "CE"),
        ],
    }

    if tipo not in intervalos or type(numero) is not int:
        raise ValueError("Tipo ou numero de questao invalido.")

    for inicio, fim, componente in intervalos[tipo]:
        if inicio <= numero <= fim:
            return componente

    raise ValueError(
        f"Questao fora dos intervalos oficiais: {tipo} {numero}"
    )
