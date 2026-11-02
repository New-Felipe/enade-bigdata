
import json
from pathlib import Path
from jsonschema import Draft202012Validator

# 1. Carrega o JSON Schema
schema_path = Path("docs/schemas/questao.schema.json")
schema = json.loads(schema_path.read_text(encoding="utf-8"))

# 2. Verifica se o próprio Schema está correto
Draft202012Validator.check_schema(schema)

validator = Draft202012Validator(schema)

# 3. Localiza os exemplos de questões
arquivos = sorted(Path("docs/exemplos").glob("questao-*.json"))

if not arquivos:
    raise SystemExit("Nenhum exemplo encontrado.")

# 4. Valida cada exemplo
for arquivo in arquivos:
    documento = json.loads(arquivo.read_text(encoding="utf-8"))

    erros = sorted(
        validator.iter_errors(documento),
        key=lambda erro: list(map(str, erro.absolute_path))
    )

    if erros:
        print(f"\nERRO: {arquivo}")

        for erro in erros:
            print(f"- {erro.message}")

        raise SystemExit(1)

    print(f"OK: {arquivo}")

# 5. Teste negativo: discursiva não pode ter alternativas
discursiva = json.loads(
    Path("docs/exemplos/questao-discursiva.json").read_text(encoding="utf-8")
)

discursiva["alternativas"] = [
    {"letra": "A", "texto": "Alternativa inválida"}
]

if list(validator.iter_errors(discursiva)):
    print("OK: regra de questão discursiva funcionando.")
else:
    raise SystemExit(
        "ERRO: o Schema aceitou alternativas em questão discursiva."
    )

print("\nTodos os testes foram concluídos com sucesso!")
