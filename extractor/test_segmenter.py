"""Testes de regressao da extracao e segmentacao ENADE."""

import unittest

from extractor.extractor import (
    extrair_paginas,
    extrair_colunas,
    limpar_texto_pagina,
)

from extractor.segmenter import (
    identificar_titulo,
    normalizar_texto,
    separar_alternativas,
    segmentar_questao_em_paginas,
    segmentar_questao_em_coluna,
    segmentar_questoes_na_mesma_pagina,
    eh_pagina_questionario,
    eh_pagina_apenas_rascunho,
    mapear_questoes_prova,
    segmentar_questao_com_continuacao,
    planejar_extracao_questoes,
    extrair_questoes_planejadas,
)

PDF = (
    "data/raw/enade/2021/sistemas_de_informacao/"
    "enade_2021_sistemas_de_informacao_prova.pdf"
)

ARQUIVO = "enade_2021_sistemas_de_informacao_prova.pdf"


class TestSegmentacaoEnade(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.paginas = extrair_paginas(PDF)

    def test_pagina_apenas_rascunho(self):
        pagina_2 = limpar_texto_pagina(
            self.paginas[1]["texto"], 2
        )
        pagina_3 = limpar_texto_pagina(
            self.paginas[2]["texto"], 3
        )

        self.assertFalse(
            eh_pagina_apenas_rascunho(pagina_2)
        )
        self.assertTrue(
            eh_pagina_apenas_rascunho(pagina_3)
        )

        self.assertFalse(
            eh_pagina_apenas_rascunho(
                pagina_3 + "\nConteudo de uma questao"
            )
        )

    def test_questao_objetiva_01(self):
        questao = segmentar_questao_em_paginas(
            self.paginas, 1, "objetiva", 5, 5, ARQUIVO
        )

        self.assertEqual(questao["numero_questao"], 1)
        self.assertEqual(questao["origem"]["pagina"], 5)
        self.assertEqual(len(questao["alternativas"]), 5)
        self.assertTrue(
            questao["texto"].startswith("A chance de uma")
        )
        self.assertTrue(
            questao["alternativas"][0]["texto"].startswith(
                "o fator ambiental"
            )
        )

    def test_questao_discursiva_01_sem_pagina_rascunho(self):
        questao = segmentar_questao_em_paginas(
            self.paginas, 1, "discursiva", 2, 3, ARQUIVO
        )

        self.assertEqual(questao["origem"]["pagina"], 2)
        self.assertEqual(questao["pagina_final"], 2)
        self.assertEqual(questao["alternativas"], [])
        self.assertIn(
            "Considerando as informações e os argumentos",
            questao["texto"],
        )
        self.assertNotIn(
            "RASCUNHO", normalizar_texto(questao["texto"]).upper()
        )

    def test_questao_discursiva_02(self):
        questao = segmentar_questao_em_paginas(
            self.paginas, 2, "discursiva", 4, 4, ARQUIVO
        )

        self.assertEqual(questao["alternativas"], [])
        self.assertIn("a) Explique", questao["texto"])
        self.assertIn("b) Apresente", questao["texto"])
        self.assertNotIn(
            "RASCUNHO", normalizar_texto(questao["texto"])
        )

    def test_questao_objetiva_multiplas_paginas(self):
        questao = segmentar_questao_em_paginas(
            self.paginas, 2, "objetiva", 6, 7, ARQUIVO
        )

        texto = normalizar_texto(questao["texto"])

        self.assertIn("TEXTO I", texto)
        self.assertIn("TEXTO II", texto)
        self.assertEqual(questao["origem"]["pagina"], 6)
        self.assertEqual(questao["pagina_final"], 7)
        self.assertEqual(
            [a["letra"] for a in questao["alternativas"]],
            list("ABCDE"),
        )
        self.assertNotIn("R272021", texto)

    def test_intervalo_invalido(self):
        with self.assertRaises(ValueError):
            segmentar_questao_em_paginas(
                self.paginas, 2, "objetiva", 7, 6, ARQUIVO
            )

    def test_questao_12_rodape_fragmentado(self):
        colunas = extrair_colunas(PDF, 19)["colunas"]

        texto = limpar_texto_pagina(
            colunas["direita"], 19
        )

        linhas = texto.splitlines()

        inicio = next(
            i for i, linha in enumerate(linhas)
            if (questao := identificar_titulo(linha))
            and questao["numero_questao"] == 12
        )

        resultado = separar_alternativas(
            "\n".join(linhas[inicio + 1:])
        )

        self.assertEqual(len(resultado["alternativas"]), 5)

        self.assertEqual(
            [a["letra"] for a in resultado["alternativas"]],
            list("ABCDE"),
        )

        self.assertEqual(
            resultado["alternativas"][-1]["texto"],
            "As asserções I e II são proposições falsas.",
        )

        self.assertNotIn(
            "informação                            19",
            texto,
        )

    def test_segmentacao_questoes_em_colunas(self):
        colunas = extrair_colunas(PDF, 19)["colunas"]
        texto_pagina = self.paginas[18]["texto"]

        for numero, nome_coluna in [
            (11, "esquerda"),
            (12, "direita"),
        ]:
            with self.subTest(numero=numero):
                questao = segmentar_questao_em_coluna(
                    texto_pagina=texto_pagina,
                    colunas=colunas,
                    numero_pagina=19,
                    nome_coluna=nome_coluna,
                    numero_questao=numero,
                    tipo_questao="objetiva",
                    arquivo_origem=ARQUIVO,
                )

                self.assertEqual(
                    questao["numero_questao"], numero
                )
                self.assertEqual(
                    questao["origem"]["pagina"], 19
                )
                self.assertEqual(
                    questao["origem"]["coluna"], nome_coluna
                )
                self.assertTrue(questao["texto"].strip())
                self.assertEqual(
                    [a["letra"] for a in questao["alternativas"]],
                    list("ABCDE"),
                )

                if numero == 12:
                    esperado = (
                        "As asser\u00e7\u00f5es I e II "
                        "s\u00e3o proposi\u00e7\u00f5es falsas."
                    )

                    self.assertEqual(
                        questao["alternativas"][-1]["texto"],
                        esperado,
                    )

    def test_multiplas_questoes_na_mesma_pagina(self):
        esperados = {
            21: {
                15: "I, III e IV.",
                16: "II, III e IV.",
            },
            30: {
                26: "I, II e IV.",
                27: "15 e 9.",
            },
        }

        for numero_pagina, respostas in esperados.items():
            with self.subTest(pagina=numero_pagina):
                questoes = segmentar_questoes_na_mesma_pagina(
                    texto_pagina=self.paginas[numero_pagina - 1]["texto"],
                    numero_pagina=numero_pagina,
                    arquivo_origem=ARQUIVO,
                )

                self.assertEqual(len(questoes), 2)
                self.assertEqual(
                    [q["numero_questao"] for q in questoes],
                    list(respostas),
                )

                for questao in questoes:
                    numero = questao["numero_questao"]
                    alternativas = questao["alternativas"]

                    self.assertEqual(
                        questao["tipo_questao"], "objetiva"
                    )
                    self.assertEqual(
                        questao["origem"]["pagina"], numero_pagina
                    )
                    self.assertEqual(
                        questao["pagina_final"], numero_pagina
                    )
                    self.assertTrue(questao["texto"].strip())
                    self.assertEqual(
                        [a["letra"] for a in alternativas],
                        list("ABCDE"),
                    )
                    self.assertEqual(
                        alternativas[-1]["texto"],
                        respostas[numero],
                    )




    def test_identificacao_questionario(self):
        esperados = {
            1: False,
            19: False,
            20: False,
            40: True,
        }

        for numero_pagina, esperado in esperados.items():
            with self.subTest(pagina=numero_pagina):
                texto = self.paginas[numero_pagina - 1]["texto"]

                resultado = eh_pagina_questionario(texto)

                self.assertEqual(resultado, esperado)




    def test_mapeamento_completo_prova(self):
        questoes = mapear_questoes_prova(self.paginas, PDF)

        objetivas = [
            q for q in questoes
            if q["tipo_questao"] == "objetiva"
        ]

        discursivas = [
            q for q in questoes
            if q["tipo_questao"] == "discursiva"
        ]

        self.assertEqual(len(questoes), 40)
        self.assertEqual(len(objetivas), 35)
        self.assertEqual(len(discursivas), 5)

        self.assertEqual(
            [q["numero_questao"] for q in objetivas],
            list(range(1, 36)),
        )

        self.assertEqual(
            [q["numero_questao"] for q in discursivas],
            list(range(1, 6)),
        )

        self.assertFalse(
            any(q["pagina"] == 40 for q in questoes)
        )

        for numero, pagina, coluna in [
            (11, 19, "esquerda"),
            (12, 19, "direita"),
            (13, 20, "esquerda"),
            (14, 20, "direita"),
        ]:
            with self.subTest(questao=numero):
                encontrados = [
                    q for q in objetivas
                    if q["numero_questao"] == numero
                ]

                self.assertEqual(len(encontrados), 1)
                self.assertEqual(encontrados[0]["pagina"], pagina)
                self.assertEqual(encontrados[0]["coluna"], coluna)

    def test_questoes_com_continuacao_na_pagina_seguinte(self):
        casos = [
            (5, 10, 11, 6),
            (29, 32, 33, 30),
        ]

        for numero, inicio, fim, proxima in casos:
            with self.subTest(questao=numero):
                questao = segmentar_questao_com_continuacao(
                    paginas=self.paginas,
                    numero_questao=numero,
                    tipo_questao="objetiva",
                    pagina_inicial=inicio,
                    pagina_continuacao=fim,
                    proxima_questao=proxima,
                    arquivo_origem=ARQUIVO,
                )

                self.assertEqual(
                    questao["numero_questao"], numero
                )
                self.assertEqual(
                    questao["tipo_questao"], "objetiva"
                )
                self.assertEqual(
                    questao["origem"]["arquivo"], ARQUIVO
                )
                self.assertEqual(
                    questao["origem"]["pagina"], inicio
                )
                self.assertEqual(
                    questao["pagina_final"], fim
                )

                self.assertTrue(questao["texto"].strip())

                alternativas = questao["alternativas"]

                self.assertEqual(
                    [a["letra"] for a in alternativas],
                    list("ABCDE"),
                )
                self.assertTrue(
                    all(a["texto"].strip() for a in alternativas)
                )


    def test_extracao_integrada_prova(self):
        mapeadas = mapear_questoes_prova(self.paginas, PDF)

        planos = planejar_extracao_questoes(
            mapeadas,
            len(self.paginas),
        )

        resultado = extrair_questoes_planejadas(
            paginas=self.paginas,
            planos=planos,
            caminho_pdf=PDF,
            arquivo_origem=ARQUIVO,
            continuacoes={
                ("objetiva", 5): (11, 6),
                ("objetiva", 29): (33, 30),
            },
        )

        extraidas = resultado["extraidas"]

        self.assertEqual(len(extraidas), 40)
        self.assertEqual(resultado["falhas"], [])

        objetivas = [
            q for q in extraidas
            if q["tipo_questao"] == "objetiva"
        ]

        discursivas = [
            q for q in extraidas
            if q["tipo_questao"] == "discursiva"
        ]

        self.assertEqual(len(objetivas), 35)
        self.assertEqual(len(discursivas), 5)

        self.assertEqual(
            sum(len(q["alternativas"]) == 5 for q in objetivas),
            34,
        )

        self.assertTrue(
            all(not q["alternativas"] for q in discursivas)
        )

        self.assertEqual(
            [
                item["numero_questao"]
                for item in resultado["revisar"]
            ],
            [33],
        )

        for numero, pagina_final in [(5, 11), (29, 33)]:
            questao = next(
                q for q in objetivas
                if q["numero_questao"] == numero
            )
            self.assertEqual(
                questao["pagina_final"],
                pagina_final,
            )

        identificadores = [
            (q["tipo_questao"], q["numero_questao"])
            for q in extraidas
        ]

        self.assertEqual(
            len(identificadores),
            len(set(identificadores)),
        )

    def test_extracao_integrada_prova(self):
        from extractor.segmenter import (
            planejar_extracao_questoes,
            extrair_questoes_planejadas,
        )

        mapeadas = mapear_questoes_prova(self.paginas, PDF)
        planos = planejar_extracao_questoes(
            mapeadas, len(self.paginas)
        )

        resultado = extrair_questoes_planejadas(
            paginas=self.paginas,
            planos=planos,
            caminho_pdf=PDF,
            arquivo_origem=ARQUIVO,
            continuacoes={
                ("objetiva", 5): (11, 6),
                ("objetiva", 29): (33, 30),
            },
        )

        extraidas = resultado["extraidas"]
        objetivas = [
            q for q in extraidas
            if q["tipo_questao"] == "objetiva"
        ]
        discursivas = [
            q for q in extraidas
            if q["tipo_questao"] == "discursiva"
        ]

        self.assertEqual(len(extraidas), 40)
        self.assertEqual(resultado["falhas"], [])
        self.assertEqual(len(objetivas), 35)
        self.assertEqual(len(discursivas), 5)
        self.assertEqual(
            sum(len(q["alternativas"]) == 5 for q in objetivas),
            34,
        )
        self.assertEqual(
            [q["numero_questao"] for q in resultado["revisar"]],
            [33],
        )

if __name__ == "__main__":
    unittest.main()
