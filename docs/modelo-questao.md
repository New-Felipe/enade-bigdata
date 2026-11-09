# Modelo Estruturado de Questão ENADE

## 1. Objetivo do modelo

Este documento define o formato canônico utilizado para representar individualmente as questões do ENADE no projeto ENADE Big Data.

Cada questão é armazenada como um documento JSON independente, contendo texto-base, enunciado, alternativas, gabarito, metadados e informações de rastreabilidade até o PDF de origem.

O modelo é independente das tecnologias do pipeline. Ele pode ser consumido pelo extrator, pelo produtor Kafka, pelo consumidor, pelo Elasticsearch e pela API, sem depender de nenhuma delas.

A definição formal está em [`docs/schemas/questao.schema.json`](schemas/questao.schema.json) (JSON Schema Draft 2020-12). As regras que comparam campos entre si não podem ser expressas apenas no Schema e são verificadas por [`scripts/validar_modelo.py`](../scripts/validar_modelo.py) (ver seção 11).

## 2. Estrutura do documento JSON

Todos os campos abaixo são aceitos; nenhum outro campo é permitido (`additionalProperties: false`).

### 2.1. Campos de primeiro nível

| Campo | Finalidade | Tipo | Obrigatório | Valores permitidos e regras de preenchimento |
|---|---|---|---|---|
| `id` | Identificador único e determinístico da questão. | String | Sim | Padrão `enade-{curso_slug}-{ano}-{tipo_conteudo}-{tipo_questao}-q{numero}`. Deve ser compatível com os demais campos (seção 3). |
| `area` | Área de conhecimento da questão. | String | Sim | Texto não vazio e sem ser composto só de espaços. Deve refletir a classificação disponível; não preencher com valores arbitrários. |
| `curso` | Nome padronizado e legível do curso. | String | Sim | Texto não vazio. Mantém acentos (ex.: `Sistemas de Informação`). Questões de Formação Geral usam `Formação Geral`. |
| `ano` | Ano da edição do ENADE. | Integer | Sim | Inteiro maior ou igual a 2004. |
| `numero_questao` | Número original da questão na prova. | Integer | Sim | Inteiro maior ou igual a 1. |
| `tipo_conteudo` | Parte da prova a que a questão pertence. | String | Sim | `FG` (Formação Geral) ou `CE` (Componente Específico). |
| `tipo_questao` | Formato da questão. | String | Sim | `objetiva` ou `discursiva`. |
| `texto_base` | Texto de apoio apresentado antes do enunciado. | String | Não | Quando presente, deve conter texto (não pode ser vazio nem só espaços). Omitir o campo quando a questão não tiver texto de apoio. |
| `enunciado` | Enunciado principal da questão. | String | Sim | Texto não vazio e sem ser composto só de espaços. |
| `alternativas` | Lista de alternativas da questão. | Array de objetos | Sim | Objetiva: duas ou mais. Discursiva: lista vazia `[]`. Ver seção 2.2. |
| `gabarito` | Alternativa correta. | String ou `null` | Sim | Uma letra, ou `null` quando indisponível ou não aplicável. O campo é obrigatório no JSON, mas aceita `null`. Ver seção 8. |
| `anulada` | Indica se a questão foi anulada oficialmente. | Boolean | Sim | `true` ou `false`. |
| `objetos_conhecimento` | Objetos de conhecimento relacionados. | Array de strings | Sim | Itens únicos, não vazios. Pode ser `[]`. |
| `competencias` | Competências relacionadas. | Array de strings | Sim | Itens únicos, não vazios. Pode ser `[]`. |
| `origem` | Rastreabilidade até o PDF. | Objeto | Sim | Ver seção 2.3. |

### 2.2. Objeto `alternativas[]`

Cada elemento da lista possui exatamente os campos abaixo.

| Campo | Finalidade | Tipo | Obrigatório | Valores permitidos e regras de preenchimento |
|---|---|---|---|---|
| `alternativas.letra` | Identifica a alternativa na prova. | String | Sim | `A`, `B`, `C`, `D` ou `E`. Não pode se repetir dentro da mesma questão. |
| `alternativas.texto` | Conteúdo da alternativa. | String | Sim | Texto não vazio e sem ser composto só de espaços. |

### 2.3. Objeto `origem`

| Campo | Finalidade | Tipo | Obrigatório | Valores permitidos e regras de preenchimento |
|---|---|---|---|---|
| `origem.arquivo` | Nome do PDF de onde a questão foi extraída. | String | Sim | Texto não vazio e sem ser composto só de espaços. |
| `origem.pagina` | Página física do PDF onde a questão está localizada. | Integer | Sim | Inteiro maior ou igual a 1 (a primeira página do PDF é a 1). |

### 2.4. Exemplo resumido

```json
{
  "id": "enade-sistemas-de-informacao-2023-ce-obj-q01",
  "area": "Computação",
  "curso": "Sistemas de Informação",
  "ano": 2023,
  "numero_questao": 1,
  "tipo_conteudo": "CE",
  "tipo_questao": "objetiva",
  "enunciado": "...",
  "alternativas": [
    { "letra": "A", "texto": "..." },
    { "letra": "B", "texto": "..." }
  ],
  "gabarito": "B",
  "anulada": false,
  "objetos_conhecimento": [],
  "competencias": [],
  "origem": { "arquivo": "enade_2023_sistemas_de_informacao_prova.pdf", "pagina": 5 }
}
```

Exemplos completos estão na seção 12.

## 3. Identificador único

O campo `id` é determinístico: o mesmo documento de origem, ao ser reprocessado, gera sempre o mesmo `id`. Isso permite evitar duplicidades.

Formato:

`enade-{curso_slug}-{ano}-{tipo_conteudo}-{tipo_questao}-q{numero}`

| Parte | Origem | Regra |
|---|---|---|
| `curso_slug` | Campo `curso` | Minúsculas, sem acentos, palavras separadas por hífen. |
| `ano` | Campo `ano` | Quatro dígitos. |
| `tipo_conteudo` | Campo `tipo_conteudo` | `fg` ou `ce`, em minúsculas. |
| `tipo_questao` | Campo `tipo_questao` | `obj` para `objetiva`; `disc` para `discursiva`. |
| `numero` | Campo `numero_questao` | Número original, com pelo menos dois dígitos (`01`, `10`, `105`). |

Exemplos:

- `enade-sistemas-de-informacao-2023-ce-obj-q01`
- `enade-sistemas-de-informacao-2023-ce-disc-q01`
- `enade-formacao-geral-2023-fg-obj-q01`

**Normalização do curso.** O slug é calculado a partir de `curso` apenas para compor o `id`; o valor de `curso` no documento não é alterado e mantém os acentos.

- `Sistemas de Informação` → `sistemas-de-informacao`
- `Formação Geral` → `formacao-geral`

**Por que `tipo_questao` faz parte do id.** Questões objetivas e discursivas podem ter o mesmo curso, ano e número. Sem esse segmento, `...-ce-q01` poderia identificar duas questões diferentes e uma sobrescreveria a outra.

**Verificação.** O Schema valida somente o formato do `id` por expressão regular. O validador Python verifica também se o `id` corresponde a `curso`, `ano`, `tipo_conteudo`, `tipo_questao` e `numero_questao`.

## 4. `tipo_conteudo` e `tipo_questao`

São duas classificações independentes:

| Campo | Pergunta que responde | Valores |
|---|---|---|
| `tipo_conteudo` | A que parte da prova a questão pertence? | `FG` (Formação Geral), `CE` (Componente Específico) |
| `tipo_questao` | Qual o formato de resposta? | `objetiva`, `discursiva` |

Qualquer combinação é possível: existem questões objetivas e discursivas tanto em FG quanto em CE.

## 5. Formação Geral e Componente Específico

- **Componente Específico (CE):** `tipo_conteudo: "CE"` e `curso` com o nome padronizado do curso.
- **Formação Geral (FG):** `tipo_conteudo: "FG"` e `curso: "Formação Geral"`.

Uma questão de Formação Geral é cadastrada **uma única vez**, independentemente de quantos cursos fizeram aquela prova. Não se criam cópias por curso.

**Razão da decisão.** A mesma questão de FG aparece nas provas de vários cursos. Duplicá-la criaria documentos repetidos, distorceria as estatísticas e dificultaria a idempotência e a indexação.

**Consulta futura.** Uma pesquisa por curso específico poderá incluir as questões de Formação Geral por meio de uma condição de consulta (por exemplo, "curso igual ao selecionado **ou** `tipo_conteudo` igual a `FG`"), sem duplicar documentos. Essa lógica de busca não faz parte desta etapa.

O validador rejeita `FG` com curso diferente de `Formação Geral` e `CE` com curso `Formação Geral`.

## 6. Questões objetivas

- `tipo_questao`: `objetiva`.
- `alternativas`: **duas ou mais** alternativas. Não se exige exatamente cinco.
- Cada alternativa tem `letra` (`A` a `E`) e `texto` não vazio.
- As letras **não podem se repetir**, mesmo que os textos sejam diferentes.
- `gabarito`: letra que corresponda a uma das alternativas existentes, ou `null` quando ainda indisponível.

## 7. Questões discursivas

- `tipo_questao`: `discursiva`.
- `alternativas`: sempre `[]`.
- `gabarito`: sempre `null`.
- `anulada`: indica a situação oficial da questão (`true` ou `false`).

### 7.1. Representações de conteúdo

Os campos textuais (`texto_base`, `enunciado`, `alternativas.texto`) podem armazenar fórmulas, diagramas e tabelas em formatos textuais como LaTeX, Mermaid ou Markdown, quando aplicável.

Este modelo não define, por ora, estruturas específicas para imagens, tabelas, diagramas ou outras mídias. Elas poderão ser incluídas em etapas posteriores.

## 8. Gabarito e anulação

O campo `gabarito` é obrigatório no JSON, mas aceita `null`.

| Situação | `alternativas` | `gabarito` | `anulada` |
|---|---|---|---|
| Objetiva não anulada, gabarito disponível | Duas ou mais | Letra de uma alternativa existente | `false` |
| Objetiva não anulada, gabarito indisponível | Duas ou mais | `null` | `false` |
| Objetiva anulada | Alternativas originais preservadas | `null` | `true` |
| Discursiva não anulada | `[]` | `null` | `false` |
| Discursiva anulada | `[]` | `null` | `true` |

Regras:

- Um gabarito preenchido precisa corresponder a uma das alternativas da própria questão (por exemplo, `Z` é rejeitado quando existem apenas A–E).
- `null` representa gabarito ainda indisponível ou não aplicável.
- Questões anuladas **permanecem no conjunto de dados**, com `anulada: true` e `gabarito: null`.
- Em questões objetivas anuladas, as alternativas originais são preservadas.
- Uma questão anulada com gabarito preenchido é rejeitada.

## 9. Objetos de conhecimento e competências

`objetos_conhecimento` e `competencias` são listas de textos. Permitem registrar mais de um assunto ou competência para a mesma questão.

- Os itens devem ser únicos e não podem ser vazios nem compostos só de espaços.
- As listas podem permanecer vazias enquanto a informação não estiver disponível.
- Não devem ser atribuídos metadados sem uma fonte que os justifique.

## 10. Rastreabilidade

O objeto `origem` permite localizar o conteúdo original:

- `arquivo`: nome do PDF de origem.
- `pagina`: página física do PDF, iniciando em 1.

## 11. Validação

O script [`scripts/validar_modelo.py`](../scripts/validar_modelo.py) executa:

1. A conferência de que o próprio Schema é válido (Draft 2020-12).
2. A validação estrutural dos exemplos de `docs/exemplos/` contra o Schema.
3. As verificações semânticas, que comparam campos entre si:
   - o `id` corresponde ao curso, ano, tipo de conteúdo, tipo de questão e número;
   - `FG` usa o curso `Formação Geral` e `CE` não o usa;
   - as letras das alternativas não se repetem;
   - o gabarito preenchido corresponde a uma alternativa;
   - regras de objetivas, discursivas e anuladas.
4. Casos de teste positivos e negativos, nos quais cada rejeição é conferida pela regra esperada.

O script encerra com código diferente de zero quando encontra uma falha. Instruções de execução estão no [README](../README.md).

> Observação: `uniqueItems` no Schema compara os objetos de `alternativas` por inteiro e, portanto, não garante a unicidade da `letra`. Essa garantia vem da verificação semântica.

## 12. Exemplos

- [Questão objetiva](exemplos/questao-objetiva.json)
- [Questão discursiva](exemplos/questao-discursiva.json)
- [JSON Schema](schemas/questao.schema.json)

Os exemplos são ilustrativos e não representam questões oficiais extraídas do acervo do ENADE.

## 13. Integração futura com o extrator

Este modelo é o **formato canônico** esperado pelo restante do pipeline (produtor Kafka, consumidor, Elasticsearch e API).

O extrator (Issue #3) produz uma representação **intermediária** diferente. Entre as incompatibilidades identificadas:

- Usa o campo `texto`, enquanto o modelo canônico separa `texto_base` e `enunciado`. O `texto` do extrator pode reunir texto-base e enunciado; **não** deve ser copiado diretamente para `enunciado` sem esse tratamento.
- Inclui campos intermediários de extração (como `pagina_final` e `validacao_extracao`) que não fazem parte do Schema.
- Não traz metadados exigidos pelo modelo, que precisam ser enriquecidos (`id`, `area`, `curso`, `ano`, `tipo_conteudo`, `gabarito`, `anulada`, `objetos_conhecimento`, `competencias`).
- Normaliza os nomes de cursos de forma diferente (por exemplo, sem acentos).

A adaptação deve acontecer na etapa de extração, ou em um adaptador, **antes** da validação e da publicação do documento canônico. O Schema não é flexibilizado para aceitar a saída intermediária.
