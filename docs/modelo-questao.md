
# Modelo Estruturado de Questão ENADE

## 1. Objetivo

Este documento define o padrão utilizado para representar individualmente as questões do ENADE no projeto ENADE Big Data.

Cada questão será armazenada como um documento JSON independente, contendo seu conteúdo, alternativas, gabarito, metadados e informações de rastreabilidade.

O modelo é independente das tecnologias utilizadas no pipeline, podendo ser consumido pelo extrator, produtor Kafka, consumidor, Elasticsearch e API.

## 2. Estrutura do documento

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| id | String | Sim | Identificador único da questão. |
| area | String | Sim | Área de conhecimento. |
| curso | String | Sim | Curso relacionado à questão. |
| ano | Integer | Sim | Ano da edição do ENADE. |
| numero_questao | Integer | Sim | Número original da questão. |
| tipo_conteudo | String | Sim | FG ou CE. |
| tipo_questao | String | Sim | Objetiva ou discursiva. |
| texto_base | String | Não | Texto de apoio, quando existente. |
| enunciado | String | Sim | Enunciado principal. |
| alternativas | Array | Sim | Lista de alternativas da questão. |
| gabarito | String ou Null | Sim | Resposta correta, quando disponível. |
| anulada | Boolean | Sim | Indica se a questão foi anulada. |
| objetos_conhecimento | Array | Sim | Objetos de conhecimento relacionados. |
| competencias | Array | Sim | Competências relacionadas. |
| origem | Object | Sim | Informações do documento de origem. |

## 3. Identificação da questão

O campo `id` utiliza um identificador determinístico.

Formato:

`enade-{curso}-{ano}-{tipo_conteudo}-q{numero}`

Exemplo:

`enade-si-2023-ce-q01`

O identificador deverá permanecer igual durante o reprocessamento do mesmo documento de origem, permitindo evitar duplicidades.

## 4. Tipos de conteúdo

O campo `tipo_conteudo` aceita:

- FG: Formação Geral.
- CE: Componente Específico.

## 5. Tipos de questão

O campo `tipo_questao` aceita:

- objetiva: questão composta por alternativas.
- discursiva: questão que exige resposta desenvolvida.

Questões objetivas devem possuir pelo menos duas alternativas.

Questões discursivas devem possuir uma lista de alternativas vazia e gabarito nulo.

## 6. Gabarito e anulação

O campo `gabarito` poderá receber:

- Uma letra correspondente à alternativa correta.
- `null`, quando o gabarito ainda não estiver disponível ou não for aplicável.

O campo `anulada` deverá ser booleano:

- `true`: questão anulada.
- `false`: questão não anulada.

Questões anuladas devem permanecer no conjunto de dados. Para elas, o gabarito será representado como `null`.

## 7. Metadados

Os campos `objetos_conhecimento` e `competencias` são listas de textos.

Eles permitem registrar mais de um assunto ou competência relacionado à mesma questão.

Caso essas informações ainda não estejam disponíveis, as listas poderão permanecer vazias.

Não devem ser atribuídos metadados sem uma fonte que os justifique.

## 8. Rastreabilidade

O objeto `origem` contém:

- `arquivo`: nome do PDF de origem.
- `pagina`: número da página física no PDF, iniciando em 1.

Essas informações permitem localizar o conteúdo original da questão.

## 9. Validação

O arquivo `schemas/questao.schema.json` define as regras de validação do documento.

Os exemplos presentes em `docs/exemplos/` demonstram a aplicação do modelo para questões objetivas e discursivas.

O JSON Schema utiliza o padrão Draft 2020-12.

## 10. Exemplos

- [Questão objetiva](exemplos/questao-objetiva.json)
- [Questão discursiva](exemplos/questao-discursiva.json)
- [JSON Schema](schemas/questao.schema.json)

Os exemplos são ilustrativos e não representam questões oficiais extraídas do acervo do ENADE.
