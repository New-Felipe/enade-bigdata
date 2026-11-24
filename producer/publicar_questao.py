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


def extrair_id_questao(questao):
    if not isinstance(questao, dict):
        raise ValueError(
            "Documento JSON invalido: esperado um objeto JSON com campo 'id'."
        )

    id_questao = questao.get("id")
    if not isinstance(id_questao, str) or not id_questao.strip():
        raise ValueError(
            "Documento JSON invalido: campo 'id' ausente ou vazio."
        )

    return id_questao


def main():
    produtor = None
    id_questao = None

    try:
        with ARQUIVO_QUESTAO.open(encoding="utf-8") as arquivo:
            questao = json.load(arquivo)

        id_questao = extrair_id_questao(questao)

        produtor = KafkaProducer(
            bootstrap_servers=SERVIDOR_KAFKA,
            acks="all",
            retries=3,
        )

        resultado = produtor.send(
            TOPICO,
            key=id_questao.encode("utf-8"),
            value=json.dumps(
                questao,
                ensure_ascii=False,
            ).encode("utf-8"),
        ).get(timeout=30)

        logger.info(
            "Questao publicada: id=%s topico=%s particao=%s offset=%s",
            id_questao,
            resultado.topic,
            resultado.partition,
            resultado.offset,
        )

    except Exception:
        logger.exception(
            "Falha ao publicar questao: id=%s arquivo=%s",
            id_questao or "<indisponivel>",
            ARQUIVO_QUESTAO.name,
        )
        raise

    finally:
        if produtor is not None:
            produtor.close()
            logger.info("Conexao do produtor encerrada.")


if __name__ == "__main__":
    main()
