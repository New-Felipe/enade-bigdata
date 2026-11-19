import unittest
from unittest.mock import Mock

from consumer.consultas import agregar_questoes, buscar_questoes
from consumer.indexacao import INDICE_QUESTOES


class TestConsultasElasticsearch(unittest.TestCase):

    def test_buscar_questoes_com_highlight(self):
        cliente = Mock()

        resposta_simulada = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_id": "questao-001",
                        "_score": 0.5,
                        "highlight": {
                            "enunciado": [
                                "Conceitos de <em>banco</em> de dados."
                            ]
                        },
                    }
                ],
            }
        }

        cliente.search.return_value = resposta_simulada

        resultado = buscar_questoes(cliente, "bancos")

        cliente.search.assert_called_once_with(
            index=INDICE_QUESTOES,
            query={
                "match": {
                    "enunciado": "bancos",
                }
            },
            highlight={
                "fields": {
                    "enunciado": {},
                }
            },
            size=10,
        )

        self.assertEqual(resultado, resposta_simulada)


    def test_buscar_questoes_com_filtros_combinados(self):
        cliente = Mock()
        cliente.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": [],
            }
        }

        buscar_questoes(
            cliente,
            "bancos",
            tamanho=5,
            ano=2023,
            curso="Sistemas de Informação",
            tipo_questao="objetiva",
        )

        cliente.search.assert_called_once_with(
            index=INDICE_QUESTOES,
            query={
                "bool": {
                    "must": [
                        {
                            "match": {
                                "enunciado": "bancos",
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"ano": 2023}},
                        {
                            "term": {
                                "curso": "Sistemas de Informação",
                            }
                        },
                        {
                            "term": {
                                "tipo_questao": "objetiva",
                            }
                        },
                    ],
                }
            },
            highlight={
                "fields": {
                    "enunciado": {},
                }
            },
            size=5,
        )


    def test_agregar_questoes(self):
        cliente = Mock()

        resposta_simulada = {
            "aggregations": {
                "por_ano": {
                    "buckets": [
                        {"key": 2023, "doc_count": 1}
                    ]
                },
                "por_curso": {
                    "buckets": [
                        {
                            "key": "Sistemas de Informação",
                            "doc_count": 1,
                        }
                    ]
                },
                "por_tipo": {
                    "buckets": [
                        {"key": "objetiva", "doc_count": 1}
                    ]
                },
            }
        }

        cliente.search.return_value = resposta_simulada

        resultado = agregar_questoes(cliente)

        cliente.search.assert_called_once_with(
            index=INDICE_QUESTOES,
            size=0,
            aggs={
                "por_ano": {
                    "terms": {
                        "field": "ano",
                    }
                },
                "por_curso": {
                    "terms": {
                        "field": "curso",
                    }
                },
                "por_tipo": {
                    "terms": {
                        "field": "tipo_questao",
                    }
                },
            },
        )

        self.assertEqual(resultado, resposta_simulada)

if __name__ == "__main__":
    unittest.main()
