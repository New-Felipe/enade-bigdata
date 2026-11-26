"""Associacao dos gabaritos oficiais as questoes extraidas."""


def associar_gabarito(questao, registros_gabarito):
    """Adiciona o gabarito oficial a uma questao intermediaria."""

    tipo = questao["tipo_questao"]
    numero = questao["numero_questao"]
    chave = (tipo, numero)

    if chave not in registros_gabarito:
        raise ValueError(
            f"Gabarito nao encontrado para {tipo} {numero}"
        )

    registro = registros_gabarito[chave]

    return {
        **questao,
        "gabarito": registro["gabarito"],
        "anulada": registro["anulada"],
    }
