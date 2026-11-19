import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from consumer import consumir_questoes as modulo
from kafka import TopicPartition


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


if __name__ == "__main__":
    unittest.main()
