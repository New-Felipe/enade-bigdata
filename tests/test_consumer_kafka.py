import base64
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch


from consumer import consumir_questoes as modulo
from consumer import dlq as modulo_dlq
from kafka import OffsetAndMetadata, TopicPartition
from producer import publicar_questao as modulo_produtor

EXEMPLO_OBJETIVA = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "exemplos"
    / "questao-objetiva.json"
)


class TestConsumidorKafka(unittest.TestCase):

    def test_falha_dlq_json_malformado_nao_confirma_offset(self):
        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=100,
            value=b'{"id":',
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([mensagem])
        produtor = Mock()

        with (
            patch.object(modulo, "KafkaConsumer", return_value=consumidor),
            patch.object(modulo, "KafkaProducer", return_value=produtor),
            patch.object(
                modulo,
                "enviar_para_dlq",
                side_effect=RuntimeError("Falha simulada na DLQ"),
            ) as enviar,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "Falha simulada na DLQ"
            ):
                modulo.main()

            enviar.assert_called_once()
            consumidor.commit.assert_not_called()
            consumidor.close.assert_called_once()
            produtor.close.assert_called_once()



    def test_falha_dlq_schema_invalido_nao_confirma_offset(self):
        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=101,
            value=b'{"id":"teste-falha-dlq"}',
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([mensagem])
        produtor = Mock()

        with (
            patch.object(modulo, "KafkaConsumer", return_value=consumidor),
            patch.object(modulo, "KafkaProducer", return_value=produtor),
            patch.object(
                modulo,
                "enviar_para_dlq",
                side_effect=RuntimeError("Falha simulada na DLQ"),
            ) as enviar,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "Falha simulada na DLQ"
            ):
                modulo.main()

            enviar.assert_called_once()
            consumidor.commit.assert_not_called()
            consumidor.close.assert_called_once()
            produtor.close.assert_called_once()


    def test_confirma_apenas_offset_da_particao_processada(self):
        consumidor = Mock()

        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=2,
            offset=6,
        )

        modulo.confirmar_mensagem(consumidor, mensagem)

        particao = TopicPartition("enade-questoes", 2)
        offsets = consumidor.commit.call_args.kwargs["offsets"]

        self.assertEqual(list(offsets), [particao])
        self.assertEqual(offsets[particao].offset, 7)

        consumidor.commit.assert_called_once()


    def test_falha_commit_propaga_excecao(self):
        consumidor = Mock()
        consumidor.commit.side_effect = RuntimeError(
            "Falha simulada no commit"
        )

        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=2,
            offset=7,
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Falha simulada no commit",
        ):
            modulo.confirmar_mensagem(consumidor, mensagem)

        consumidor.commit.assert_called_once()


    def test_reprocessa_mensagem_apos_falha_temporaria_dlq(self):
        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=100,
            value=b'{"id":',
        )

        primeiro_consumidor = MagicMock()
        primeiro_consumidor.__iter__.return_value = iter([mensagem])

        segundo_consumidor = MagicMock()
        segundo_consumidor.__iter__.return_value = iter([mensagem])

        produtor = Mock()

        with (
            patch.object(
                modulo,
                "KafkaConsumer",
                side_effect=[primeiro_consumidor, segundo_consumidor],
            ),
            patch.object(
                modulo,
                "KafkaProducer",
                return_value=produtor,
            ),
            patch.object(
                modulo,
                "enviar_para_dlq",
                side_effect=[
                    RuntimeError("Falha temporaria na DLQ"),
                    None,
                ],
            ) as enviar,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Falha temporaria na DLQ",
            ):
                modulo.main()

            primeiro_consumidor.commit.assert_not_called()

            modulo.main()

            particao = TopicPartition("enade-questoes", 0)
            offsets = segundo_consumidor.commit.call_args.kwargs["offsets"]

            self.assertEqual(offsets[particao].offset, 101)
            segundo_consumidor.commit.assert_called_once()

            self.assertEqual(enviar.call_count, 2)

            primeiro_consumidor.close.assert_called_once()
            segundo_consumidor.close.assert_called_once()

    def test_mensagem_value_none_encaminha_para_dlq_e_confirma_offset(self):
        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=1,
            offset=10,
            key=b"chave-nula",
            value=None,
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([mensagem])

        produtor_dlq = Mock()
        produtor_dlq.send.return_value.get.return_value = SimpleNamespace(
            topic=modulo_dlq.TOPICO_DLQ,
            partition=0,
            offset=0,
        )

        with (
            patch.object(modulo, "KafkaConsumer", return_value=consumidor),
            patch.object(modulo, "KafkaProducer", return_value=produtor_dlq),
            patch.object(modulo, "Elasticsearch", return_value=Mock()) as cliente_es,
        ):
            modulo.main()

        cliente_es.return_value.close.assert_called_once()
        produtor_dlq.send.assert_called_once()

        topico_envio = produtor_dlq.send.call_args.args[0]
        kwargs_envio = produtor_dlq.send.call_args.kwargs
        registro = json.loads(kwargs_envio["value"].decode("utf-8"))

        self.assertEqual(topico_envio, modulo_dlq.TOPICO_DLQ)
        self.assertEqual(kwargs_envio["key"], b"chave-nula")
        self.assertEqual(registro["topico_origem"], "enade-questoes")
        self.assertEqual(registro["particao_origem"], 1)
        self.assertEqual(registro["offset_origem"], 10)
        self.assertIn("value=None", registro["erro"])
        self.assertIsNone(registro["conteudo_original_base64"])

        particao = TopicPartition("enade-questoes", 1)
        offsets = consumidor.commit.call_args.kwargs["offsets"]
        self.assertEqual(list(offsets), [particao])
        self.assertEqual(offsets[particao].offset, 11)
        consumidor.commit.assert_called_once()

    def test_mensagem_value_none_com_falha_dlq_nao_confirma_offset(self):
        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=12,
            key=None,
            value=None,
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([mensagem])
        produtor = Mock()

        with (
            patch.object(modulo, "KafkaConsumer", return_value=consumidor),
            patch.object(modulo, "KafkaProducer", return_value=produtor),
            patch.object(
                modulo,
                "enviar_para_dlq",
                side_effect=RuntimeError("Falha simulada na DLQ"),
            ) as enviar,
            self.assertLogs(modulo.logger, level="ERROR") as logs,
        ):
            with self.assertRaisesRegex(RuntimeError, "Falha simulada na DLQ"):
                modulo.main()

        enviar.assert_called_once()
        consumidor.commit.assert_not_called()
        consumidor.close.assert_called_once()
        produtor.close.assert_called_once()
        self.assertTrue(
            any("Falha ao publicar mensagem na DLQ" in linha for linha in logs.output)
        )

    def test_dlq_distingue_payload_ausente_de_payload_vazio(self):
        msg_ausente = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=20,
            key=b"k1",
            value=None,
        )
        msg_vazia = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=21,
            key=b"k2",
            value=b"",
        )
        msg_bytes = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=22,
            key=b"k3",
            value=b'{"id":',
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([msg_ausente, msg_vazia, msg_bytes])

        produtor_dlq = Mock()
        produtor_dlq.send.return_value.get.return_value = SimpleNamespace(
            topic=modulo_dlq.TOPICO_DLQ,
            partition=0,
            offset=0,
        )

        with (
            patch.object(modulo, "KafkaConsumer", return_value=consumidor),
            patch.object(modulo, "KafkaProducer", return_value=produtor_dlq),
        ):
            modulo.main()

        self.assertEqual(produtor_dlq.send.call_count, 3)

        registros = [
            json.loads(chamada.kwargs["value"].decode("utf-8"))
            for chamada in produtor_dlq.send.call_args_list
        ]

        # None -> null em JSON e motivo explicito de payload ausente
        self.assertIsNone(registros[0]["conteudo_original_base64"])
        self.assertIn("Payload ausente", registros[0]["erro"])

        # b"" -> string vazia em Base64 (distinta de None) e erro de JSONDecodeError
        self.assertEqual(registros[1]["conteudo_original_base64"], "")
        self.assertIsNotNone(registros[1]["conteudo_original_base64"])
        self.assertNotIn("Payload ausente", registros[1]["erro"])

        # bytes nao vazios -> compatibilidade Base64 preservada
        self.assertEqual(
            base64.b64decode(registros[2]["conteudo_original_base64"]),
            b'{"id":',
        )

        self.assertEqual(consumidor.commit.call_count, 3)


    def test_documento_valido_indexado_sem_envio_dlq(self):
        conteudo = EXEMPLO_OBJETIVA.read_bytes()
        questao = json.loads(conteudo.decode("utf-8"))

        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=2,
            offset=41,
            key=questao["id"].encode("utf-8"),
            value=conteudo,
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([mensagem])

        produtor = Mock()
        cliente_es = Mock()

        with (
            patch.object(
                modulo, "KafkaConsumer", return_value=consumidor
            ),
            patch.object(
                modulo, "KafkaProducer", return_value=produtor
            ),
            patch.object(
                modulo, "Elasticsearch", return_value=cliente_es
            ),
            patch.object(
                modulo, "enviar_para_dlq"
            ) as enviar,
            patch.object(
                modulo,
                "indexar_questao",
                return_value={"result": "created"},
            ) as indexar,
        ):
            modulo.main()

        indexar.assert_called_once_with(cliente_es, questao)
        enviar.assert_not_called()

        particao = TopicPartition("enade-questoes", 2)
        offsets = consumidor.commit.call_args.kwargs["offsets"]

        self.assertEqual(list(offsets), [particao])
        self.assertEqual(offsets[particao].offset, 42)

        consumidor.commit.assert_called_once()
        consumidor.close.assert_called_once()
        produtor.close.assert_called_once()
        cliente_es.close.assert_called_once()



    def test_reprocessamento_mesmo_id_indexa_e_confirma_offsets(self):
        conteudo = EXEMPLO_OBJETIVA.read_bytes()
        questao = json.loads(conteudo.decode("utf-8"))

        mensagem_1 = SimpleNamespace(
            topic="enade-questoes",
            partition=1,
            offset=30,
            key=questao["id"].encode("utf-8"),
            value=conteudo,
        )

        mensagem_2 = SimpleNamespace(
            topic="enade-questoes",
            partition=1,
            offset=31,
            key=questao["id"].encode("utf-8"),
            value=conteudo,
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter(
            [mensagem_1, mensagem_2]
        )

        produtor = Mock()
        cliente_es = Mock()

        with (
            patch.object(
                modulo, "KafkaConsumer", return_value=consumidor
            ),
            patch.object(
                modulo, "KafkaProducer", return_value=produtor
            ),
            patch.object(
                modulo, "Elasticsearch", return_value=cliente_es
            ),
            patch.object(modulo, "enviar_para_dlq") as enviar,
            patch.object(
                modulo,
                "indexar_questao",
                side_effect=[
                    {"result": "created"},
                    {"result": "updated"},
                ],
            ) as indexar,
        ):
            modulo.main()

        self.assertEqual(indexar.call_count, 2)

        for chamada in indexar.call_args_list:
            self.assertEqual(chamada.args, (cliente_es, questao))

        enviar.assert_not_called()

        particao = TopicPartition("enade-questoes", 1)

        offsets_confirmados = [
            chamada.kwargs["offsets"][particao].offset
            for chamada in consumidor.commit.call_args_list
        ]

        self.assertEqual(offsets_confirmados, [31, 32])
        self.assertEqual(consumidor.commit.call_count, 2)

        consumidor.close.assert_called_once()
        produtor.close.assert_called_once()
        cliente_es.close.assert_called_once()


    def test_documento_semanticamente_invalido_encaminhado_para_dlq(self):
        questao = json.loads(EXEMPLO_OBJETIVA.read_text(encoding="utf-8"))
        questao["gabarito"] = "Z"

        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=55,
            key=questao["id"].encode("utf-8"),
            value=json.dumps(questao, ensure_ascii=False).encode("utf-8"),
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([mensagem])

        produtor_dlq = Mock()
        produtor_dlq.send.return_value.get.return_value = SimpleNamespace(
            topic=modulo_dlq.TOPICO_DLQ,
            partition=0,
            offset=0,
        )

        with (
            patch.object(modulo, "KafkaConsumer", return_value=consumidor),
            patch.object(modulo, "KafkaProducer", return_value=produtor_dlq),
            patch.object(modulo, "Elasticsearch", return_value=Mock()),
            patch.object(modulo, "indexar_questao") as indexar,
        ):
            modulo.main()

        indexar.assert_not_called()
        produtor_dlq.send.assert_called_once()
        registro = json.loads(
            produtor_dlq.send.call_args.kwargs["value"].decode("utf-8")
        )
        self.assertIn("não corresponde a nenhuma alternativa", registro["erro"])
        self.assertEqual(
            base64.b64decode(registro["conteudo_original_base64"]),
            mensagem.value,
        )

        particao = TopicPartition("enade-questoes", 0)
        offsets = consumidor.commit.call_args.kwargs["offsets"]
        self.assertEqual(offsets[particao].offset, 56)

    def test_falha_fechamento_consumidor_tenta_fechar_produtor_e_preserva_excecao(self):
        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=0,
            offset=70,
            key=None,
            value=b'{"id":',
        )

        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([mensagem])
        consumidor.close.side_effect = RuntimeError("Falha ao fechar consumidor")
        produtor = Mock()

        with (
            patch.object(modulo, "KafkaConsumer", return_value=consumidor),
            patch.object(modulo, "KafkaProducer", return_value=produtor),
            patch.object(
                modulo,
                "enviar_para_dlq",
                side_effect=RuntimeError("Falha original na DLQ"),
            ),
            self.assertLogs(modulo.logger, level="ERROR") as logs,
        ):
            with self.assertRaisesRegex(RuntimeError, "Falha original na DLQ"):
                modulo.main()

        consumidor.close.assert_called_once()
        produtor.close.assert_called_once()
        self.assertTrue(
            any("Falha ao encerrar consumidor Kafka" in l for l in logs.output)
        )

    def test_falha_fechamento_consumidor_em_execucao_normal_tenta_fechar_produtor(self):
        consumidor = MagicMock()
        consumidor.__iter__.return_value = iter([])
        consumidor.close.side_effect = RuntimeError("Falha ao fechar consumidor")
        produtor = Mock()

        with (
            patch.object(modulo, "KafkaConsumer", return_value=consumidor),
            patch.object(modulo, "KafkaProducer", return_value=produtor),
            self.assertLogs(modulo.logger, level="ERROR") as logs,
        ):
            with self.assertRaisesRegex(RuntimeError, "Falha ao fechar consumidor"):
                modulo.main()

        consumidor.close.assert_called_once()
        produtor.close.assert_called_once()
        self.assertTrue(
            any("Falha ao encerrar consumidor Kafka" in l for l in logs.output)
        )

    def test_falha_commit_registra_log_error_com_contexto(self):
        consumidor = Mock()
        consumidor.commit.side_effect = RuntimeError("Falha simulada no commit")

        mensagem = SimpleNamespace(
            topic="enade-questoes",
            partition=2,
            offset=7,
        )

        with self.assertLogs(modulo.logger, level="ERROR") as logs:
            with self.assertRaisesRegex(RuntimeError, "Falha simulada no commit"):
                modulo.confirmar_mensagem(consumidor, mensagem)

        self.assertTrue(
            any(
                "Falha ao confirmar offset" in l
                and "particao=2" in l
                and "offset=7" in l
                for l in logs.output
            )
        )

    def test_falha_indexacao_nao_confirma_offset(self):
                caminho = (
                    modulo.RAIZ_PROJETO
                    / "docs"
                    / "exemplos"
                    / "questao-objetiva.json"
                )

                questao = json.loads(caminho.read_text(encoding="utf-8"))

                mensagem = SimpleNamespace(
                    topic="enade-questoes",
                    partition=2,
                    offset=200,
                    value=json.dumps(
                        questao,
                        ensure_ascii=False,
                    ).encode("utf-8"),
                )

                consumidor = MagicMock()
                consumidor.__iter__.return_value = iter([mensagem])

                produtor = Mock()
                cliente_es = Mock()

                with (
                    patch.object(
                        modulo,
                        "KafkaConsumer",
                        return_value=consumidor,
                    ),
                    patch.object(
                        modulo,
                        "KafkaProducer",
                        return_value=produtor,
                    ),
                    patch.object(
                        modulo,
                        "Elasticsearch",
                        return_value=cliente_es,
                    ),
                    patch.object(
                        modulo,
                        "indexar_questao",
                        side_effect=RuntimeError(
                            "Falha simulada no Elasticsearch"
                        ),
                    ) as indexar,
                ):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "Falha simulada no Elasticsearch",
                    ):
                        modulo.main()

                    indexar.assert_called_once_with(cliente_es, questao)

                    consumidor.commit.assert_not_called()

                    consumidor.close.assert_called_once()
                    produtor.close.assert_called_once()
                    cliente_es.close.assert_called_once()


    def test_indexacao_sucesso_confirma_offset(self):
                caminho = (
                    modulo.RAIZ_PROJETO
                    / "docs"
                    / "exemplos"
                    / "questao-objetiva.json"
                )

                questao = json.loads(caminho.read_text(encoding="utf-8"))

                mensagem = SimpleNamespace(
                    topic="enade-questoes",
                    partition=2,
                    offset=200,
                    value=json.dumps(
                        questao,
                        ensure_ascii=False,
                    ).encode("utf-8"),
                )

                consumidor = MagicMock()
                consumidor.__iter__.return_value = iter([mensagem])

                produtor = Mock()
                cliente_es = Mock()

                with (
                    patch.object(
                        modulo,
                        "KafkaConsumer",
                        return_value=consumidor,
                    ),
                    patch.object(
                        modulo,
                        "KafkaProducer",
                        return_value=produtor,
                    ),
                    patch.object(
                        modulo,
                        "Elasticsearch",
                        return_value=cliente_es,
                    ),
                    patch.object(
                        modulo,
                        "indexar_questao",
                        return_value={"result": "created"},
                    ) as indexar,
                ):
                    modulo.main()

                    indexar.assert_called_once_with(cliente_es, questao)

                    consumidor.commit.assert_called_once_with(
                        offsets={
                            TopicPartition(
                                "enade-questoes", 2
                            ): OffsetAndMetadata(201, "")
                        }
                    )

                    consumidor.close.assert_called_once()
                    produtor.close.assert_called_once()
                    cliente_es.close.assert_called_once()


class TestProdutorKafka(unittest.TestCase):

    def test_produtor_rejeita_documento_sem_id_sem_mascarar_erro(self):
        with tempfile.TemporaryDirectory() as diretorio_temp:
            arquivo = Path(diretorio_temp) / "sem_id.json"
            arquivo.write_text(
                json.dumps({"numero_questao": 1, "tipo_questao": "objetiva"}),
                encoding="utf-8",
            )

            with (
                patch.object(modulo_produtor, "ARQUIVO_QUESTAO", arquivo),
                patch.object(modulo_produtor, "KafkaProducer") as fabrica_produtor,
                self.assertLogs(modulo_produtor.logger, level="ERROR") as logs,
            ):
                with self.assertRaisesRegex(ValueError, "campo 'id' ausente ou vazio"):
                    modulo_produtor.main()

            fabrica_produtor.assert_not_called()
            self.assertTrue(
                any("Falha ao publicar questao" in l for l in logs.output)
            )

    def test_produtor_rejeita_id_somente_espacos_e_json_nao_objeto(self):
        casos = [
            ({"id": "   "}, "campo 'id' ausente ou vazio"),
            (["nao", "objeto"], "esperado um objeto JSON"),
        ]

        with tempfile.TemporaryDirectory() as diretorio_temp:
            for indice, (conteudo, trecho_esperado) in enumerate(casos):
                arquivo = Path(diretorio_temp) / f"caso_{indice}.json"
                arquivo.write_text(json.dumps(conteudo), encoding="utf-8")

                with (
                    patch.object(modulo_produtor, "ARQUIVO_QUESTAO", arquivo),
                    patch.object(modulo_produtor, "KafkaProducer") as fabrica_produtor,
                    self.assertLogs(modulo_produtor.logger, level="ERROR"),
                ):
                    with self.assertRaisesRegex(ValueError, trecho_esperado):
                        modulo_produtor.main()

                fabrica_produtor.assert_not_called()

    def test_produtor_publica_com_chave_id_e_fecha_conexao_em_falha_de_envio(self):
        produtor = Mock()
        produtor.send.return_value.get.side_effect = RuntimeError("Broker indisponivel")

        with (
            patch.object(modulo_produtor, "ARQUIVO_QUESTAO", EXEMPLO_OBJETIVA),
            patch.object(modulo_produtor, "KafkaProducer", return_value=produtor),
            self.assertLogs(modulo_produtor.logger, level="ERROR") as logs,
        ):
            with self.assertRaisesRegex(RuntimeError, "Broker indisponivel"):
                modulo_produtor.main()

        produtor.send.assert_called_once()
        self.assertEqual(
            produtor.send.call_args.kwargs["key"],
            b"enade-sistemas-de-informacao-2023-ce-obj-q01",
        )
        produtor.close.assert_called_once()
        self.assertTrue(
            any("enade-sistemas-de-informacao-2023-ce-obj-q01" in l for l in logs.output)
        )


if __name__ == "__main__":
    unittest.main()
