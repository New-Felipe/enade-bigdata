import json
import sys
import logging
from pathlib import Path

from jsonschema import Draft202012Validator
from kafka import (
    KafkaConsumer,
    KafkaProducer,
    OffsetAndMetadata,
    TopicPartition,
)

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

from scripts.validar_modelo import validar_documento
from consumer.dlq import enviar_para_dlq
from consumer.idempotencia import registrar_se_nova

TOPICO = "enade-questoes"
SERVIDOR_KAFKA = "localhost:29092"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logging.getLogger("kafka").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

CAMINHO_SCHEMA = (
    RAIZ_PROJETO / "docs" / "schemas" / "questao.schema.json"
)


def confirmar_mensagem(consumidor, mensagem):
    particao = TopicPartition(
        mensagem.topic,
        mensagem.partition,
    )

    proximo_offset = mensagem.offset + 1

    consumidor.commit(
        offsets={
            particao: OffsetAndMetadata(
                proximo_offset,
                "",
            )
        }
    )


def main():
    schema = json.loads(CAMINHO_SCHEMA.read_text(encoding="utf-8"))
    validador = Draft202012Validator(schema)

    consumidor = KafkaConsumer(
        TOPICO,
        bootstrap_servers=SERVIDOR_KAFKA,
        group_id="enade-validacao",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=30000,
    )

    produtor_dlq = KafkaProducer(
        bootstrap_servers=SERVIDOR_KAFKA,
        acks="all",
        retries=3,
    )

    logger.info("Consumidor iniciado. Topico: %s", TOPICO)

    try:
        for mensagem in consumidor:
            try:
                questao = json.loads(mensagem.value.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as erro:
                logger.warning(
                    "Mensagem invalida: %s | particao=%s offset=%s",
                    erro,
                    mensagem.partition,
                    mensagem.offset,
                )

                enviar_para_dlq(produtor_dlq, mensagem, str(erro))
                confirmar_mensagem(consumidor, mensagem)

                logger.info("Mensagem encaminhada a DLQ.")
                continue

            erros = validar_documento(validador, questao)

            if erros:
                logger.warning(
                    "Questao rejeitada: %s",
                    "; ".join(erros),
                )

                enviar_para_dlq(
                    produtor_dlq,
                    mensagem,
                    "; ".join(erros),
                )
                confirmar_mensagem(consumidor, mensagem)

                logger.info("Questao invalida encaminhada a DLQ.")
                continue

            if not registrar_se_nova(questao["id"]):
                logger.info(
                    "Questao duplicada: id=%s",
                    questao["id"],
                )
                confirmar_mensagem(consumidor, mensagem)
                continue

            logger.info(
                "Questao validada e registrada localmente: "
                "id=%s curso=%s topico=%s particao=%s offset=%s",
                questao["id"],
                questao["curso"],
                mensagem.topic,
                mensagem.partition,
                mensagem.offset,
            )

            confirmar_mensagem(consumidor, mensagem)

    finally:
        consumidor.close()
        produtor_dlq.close()
        logger.info("Conexoes do consumidor encerradas.")



if __name__ == "__main__":
    main()
