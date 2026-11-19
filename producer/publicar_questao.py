import json
import logging
from pathlib import Path

from kafka import KafkaProducer

TOPICO = "enade-questoes"
SERVIDOR_KAFKA = "localhost:29092"

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_QUESTAO = (
    RAIZ_PROJETO / "docs" / "exemplos" / "questao-objetiva.json"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logging.getLogger("kafka").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    with ARQUIVO_QUESTAO.open(encoding="utf-8") as arquivo:
        questao = json.load(arquivo)

    produtor = KafkaProducer(
        bootstrap_servers=SERVIDOR_KAFKA,
        acks="all",
        retries=3,
    )

    try:
        resultado = produtor.send(
            TOPICO,
            key=questao["id"].encode("utf-8"),
            value=json.dumps(
                questao,
                ensure_ascii=False,
            ).encode("utf-8"),
        ).get(timeout=30)

        logger.info(
            "Questao publicada: id=%s topico=%s particao=%s offset=%s",
            questao["id"],
            resultado.topic,
            resultado.partition,
            resultado.offset,
        )

    except Exception:
        logger.exception(
            "Falha ao publicar questao: id=%s",
            questao["id"],
        )
        raise

    finally:
        produtor.close()
        logger.info("Conexao do produtor encerrada.")


if __name__ == "__main__":
    main()
