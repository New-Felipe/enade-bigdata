import sqlite3
from contextlib import closing
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

CAMINHO_BANCO = (
    RAIZ_PROJETO / "data" / "processed" / "idempotencia.sqlite3"
)


def registrar_se_nova(id_questao):
    CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(CAMINHO_BANCO)) as conexao:
        with conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS questoes_processadas (
                    id TEXT PRIMARY KEY
                )
                """
            )

            resultado = conexao.execute(
                """
                INSERT OR IGNORE INTO questoes_processadas (id)
                VALUES (?)
                """,
                (id_questao,),
            )

            return resultado.rowcount == 1
