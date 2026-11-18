import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from kafka import KafkaConsumer

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

from scripts.validar_modelo import validar_documento

TOPICO = "enade-questoes"
SERVIDOR_KAFKA = "localhost:29092"

CAMINHO_SCHEMA = (
    RAIZ_PROJETO / "docs" / "schemas" / "questao.schema.json"
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

    print(f"Aguardando questões no tópico '{TOPICO}'...")

    try:
        for mensagem in consumidor:
            try:
                questao = json.loads(mensagem.value.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as erro:
                print(f"Mensagem inválida: {erro}")
                raise SystemExit(1) from erro

            erros = validar_documento(validador, questao)

            if erros:
                print("Questão rejeitada:")
                for erro in erros:
                    print(f"  - {erro}")
                raise SystemExit(1)

            print("Questão validada com sucesso!")
            print(f"ID: {questao['id']}")
            print(f"Curso: {questao['curso']}")
            print(f"Tópico: {mensagem.topic}")
            print(f"Partição: {mensagem.partition}")
            print(f"Offset: {mensagem.offset}")

            consumidor.commit()

    finally:
        consumidor.close()


if __name__ == "__main__":
    main()
