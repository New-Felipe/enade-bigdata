import json
from pathlib import Path

from kafka import KafkaProducer

TOPICO = "enade-questoes"
SERVIDOR_KAFKA = "localhost:29092"

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_QUESTAO = RAIZ_PROJETO / "docs" / "exemplos" / "questao-objetiva.json"

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
                questao, ensure_ascii=False
            ).encode("utf-8"),
        ).get(timeout=30)

        print("Questão publicada com sucesso!")
        print(f"ID: {questao['id']}")
        print(f"Tópico: {resultado.topic}")
        print(f"Partição: {resultado.partition}")
        print(f"Offset: {resultado.offset}")
    finally:
        produtor.close()


if __name__ == "__main__":
    main()