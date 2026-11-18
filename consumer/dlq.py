import base64
import json

TOPICO_DLQ = "enade-questoes-dlq"


def enviar_para_dlq(produtor, mensagem, motivo):
    registro = {
        "topico_origem": mensagem.topic,
        "particao_origem": mensagem.partition,
        "offset_origem": mensagem.offset,
        "erro": motivo,
        "conteudo_original_base64": base64.b64encode(
            mensagem.value
        ).decode("ascii"),
    }

    resultado = produtor.send(
        TOPICO_DLQ,
        key=mensagem.key,
        value=json.dumps(
            registro, ensure_ascii=False
        ).encode("utf-8"),
    ).get(timeout=30)

    return resultado
