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

    try:
        consumidor.commit(
            offsets={
                particao: OffsetAndMetadata(
                    proximo_offset,
                    "",
                )
            }
        )
    except Exception:
        logger.exception(
            "Falha ao confirmar offset | topico=%s particao=%s offset=%s proximo_offset=%s",
            mensagem.topic,
            mensagem.partition,
            mensagem.offset,
            proximo_offset,
        )
        raise


def _publicar_na_dlq(produtor_dlq, mensagem, motivo):
    try:
        return enviar_para_dlq(produtor_dlq, mensagem, motivo)
    except Exception:
        logger.exception(
            "Falha ao publicar mensagem na DLQ | topico=%s particao=%s offset=%s",
            mensagem.topic,
            mensagem.partition,
            mensagem.offset,
        )
        raise


def _encerrar_recurso(nome, recurso):
    if recurso is None:
        return None

    try:
        recurso.close()
        return None
    except Exception as erro:
        logger.exception("Falha ao encerrar %s.", nome)
        return erro


def main():
    schema = json.loads(CAMINHO_SCHEMA.read_text(encoding="utf-8"))
    validador = Draft202012Validator(schema)

    consumidor = None
    produtor_dlq = None
    erro_original = None

    try:
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

        for mensagem in consumidor:
            if mensagem.value is None:
                motivo = "Payload ausente (value=None)"
                logger.warning(
                    "Mensagem com payload ausente | topico=%s particao=%s offset=%s",
                    mensagem.topic,
                    mensagem.partition,
                    mensagem.offset,
                )

                _publicar_na_dlq(produtor_dlq, mensagem, motivo)
                confirmar_mensagem(consumidor, mensagem)

                logger.info("Mensagem com payload ausente encaminhada a DLQ.")
                continue

            try:
                questao = json.loads(mensagem.value.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as erro:
                logger.warning(
                    "Mensagem invalida: %s | particao=%s offset=%s",
                    erro,
                    mensagem.partition,
                    mensagem.offset,
                )

                _publicar_na_dlq(produtor_dlq, mensagem, str(erro))
                confirmar_mensagem(consumidor, mensagem)

                logger.info("Mensagem encaminhada a DLQ.")
                continue

            try:
                erros = validar_documento(validador, questao)
            except Exception:
                logger.exception(
                    "Falha inesperada na validacao da mensagem | topico=%s particao=%s offset=%s",
                    mensagem.topic,
                    mensagem.partition,
                    mensagem.offset,
                )
                raise

            if erros:
                logger.warning(
                    "Questao rejeitada: %s",
                    "; ".join(erros),
                )

                _publicar_na_dlq(
                    produtor_dlq,
                    mensagem,
                    "; ".join(erros),
                )
                confirmar_mensagem(consumidor, mensagem)

                logger.info("Questao invalida encaminhada a DLQ.")
                continue

            try:
                nova = registrar_se_nova(questao["id"])
            except Exception:
                logger.exception(
                    "Falha inesperada na deduplicacao local | id=%s topico=%s particao=%s offset=%s",
                    questao["id"],
                    mensagem.topic,
                    mensagem.partition,
                    mensagem.offset,
                )
                raise

            if not nova:
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

    except Exception as erro:
        erro_original = erro
        raise

    finally:
        erro_consumidor = _encerrar_recurso("consumidor Kafka", consumidor)
        erro_produtor = _encerrar_recurso("produtor DLQ", produtor_dlq)
        logger.info("Conexoes do consumidor encerradas.")

        if erro_original is None:
            erro_fechamento = erro_consumidor or erro_produtor
            if erro_fechamento is not None:
                raise erro_fechamento



if __name__ == "__main__":
    main()
