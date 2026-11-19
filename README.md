
# ENADE Big Data

Plataforma distribuída para processamento, indexação e busca sobre o acervo histórico de provas do ENADE.

O projeto tem como objetivo transformar provas em PDF em documentos estruturados e pesquisáveis, utilizando processamento distribuído, mensageria, indexação full-text, cache e autenticação com perfis de acesso.

## Arquitetura do projeto

Fluxo principal:

PDFs → Extração e Estruturação → Apache Kafka → Elasticsearch → API / Redis → Cliente Web

O Apache Kafka é responsável pelo transporte das questões estruturadas entre os serviços.

### Pipeline Kafka

1. O produtor publica questões ENADE em formato JSON.
2. As mensagens são enviadas ao tópico `enade-questoes`.
3. O consumidor recebe e valida os documentos.
4. Mensagens inválidas são encaminhadas à Dead Letter Queue (DLQ).
5. Questões válidas passam pela verificação de duplicação local.
6. O consumidor confirma os offsets após o tratamento das mensagens.

A integração com Elasticsearch para persistência definitiva dos documentos está prevista na Issue #49.

### Segurança prevista

- LDAP para autenticação de usuários e perfis de acesso.
- Kerberos para autenticação entre serviços.

Essas funcionalidades fazem parte da arquitetura planejada e ainda não estão implementadas no pipeline Kafka local.

## Tecnologias

- Python
- Apache Kafka 3.9.1
- kafka-python 3.0.13
- JSON Schema / jsonschema 4.26.0
- SQLite
- Elasticsearch
- Redis
- Docker / Docker Compose
- LDAP e Kerberos (planejados)
- FastAPI (planejado)
- Frontend web (a definir)

## Estrutura do projeto

```text
.
├── api/
├── consumer/
│   ├── consumir_questoes.py
│   ├── dlq.py
│   └── idempotencia.py
├── data/
│   ├── processed/
│   └── raw/
├── docs/
│   ├── exemplos/
│   ├── schemas/
│   └── modelo-questao.md
├── extractor/
├── frontend/
├── producer/
│   └── publicar_questao.py
├── scripts/
│   └── validar_modelo.py
├── security/
│   ├── kerberos/
│   └── ldap/
├── tests/
│   └── test_consumer_kafka.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Funcionalidades implementadas

### Modelo estruturado de questões

- Modelo JSON para questões objetivas e discursivas.
- Validação com JSON Schema.
- Validações semânticas adicionais.
- Exemplos de documentos ENADE.

### Mensageria com Apache Kafka — Issue #48

- Produtor de questões estruturadas em JSON.
- Consumidor com validação das mensagens.
- Tópico principal `enade-questoes`.
- Dead Letter Queue `enade-questoes-dlq`.
- Particionamento por chave da mensagem.
- Grupo de consumidores `enade-validacao`.
- Deduplicação local com SQLite.
- Confirmação manual de offsets por partição.
- Tratamento de falhas no envio à DLQ.
- Recuperação após falha controlada.
- Logs estruturados de publicação e consumo.
- Testes automatizados do consumidor.

A deduplicação local com SQLite foi desenvolvida como protótipo na Issue #48.
Na implementação atual, o consumidor utiliza o Elasticsearch como destino
de persistência, identificando os documentos pelo ID da questão.

### Indexação e consultas com Elasticsearch — Issue #49

- Elasticsearch 8.15.3 executado em contêiner Docker.
- Índice `enade-questoes` com mapping estruturado.
- Analisador `brazilian` para pesquisas textuais em português.
- Integração entre consumidor Kafka e Elasticsearch.
- Validação das questões antes da indexação.
- Identificadores determinísticos para evitar documentos duplicados.
- Atualização do documento quando o mesmo ID é reprocessado.
- Confirmação manual do offset após indexação bem-sucedida.
- Preservação do offset em caso de falha na indexação.
- Recuperação de mensagens pendentes após falhas.
- Busca textual por enunciado com pontuação de relevância.
- Filtros combinados por ano, curso e tipo de questão.
- Highlight para destacar os termos encontrados.
- Agregações estatísticas por ano, curso e tipo de questão.
- Testes automatizados de consultas e integração com Kafka.

## Funcionalidades planejadas

- Extração de questões de provas do ENADE.
- Segmentação de cada questão em documentos independentes.
- Tratamento de fórmulas, diagramas, tabelas e imagens.
- Ampliação das consultas para filtros por área e competência.
- Ampliação da busca textual para texto-base, alternativas e outros campos.
- Cache de consultas com Redis.
- Sessão e lista de questões.
- Perfis de acesso para Estudante e Professor.
- Exportação de questões em PDF ou JSON.
- Integração de autenticação e segurança entre serviços.

## Execução

Os comandos abaixo foram preparados para Windows com PowerShell, a partir da raiz do repositório.

### 1. Iniciar a infraestrutura

```powershell
docker compose up -d
```

Verificar os containers:

```powershell
docker compose ps
```

O ambiente utiliza Kafka, Elasticsearch e Redis.

### 2. Preparar o ambiente Python

Criar o ambiente virtual, caso ainda não exista:

```powershell
py -m venv .venv
```

Instalar as dependências:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configurar os tópicos Kafka

O ambiente utiliza um broker Kafka com persistência em volume Docker.

Portas utilizadas:

- `localhost:29092`: comunicação dos programas executados no Windows.
- `kafka:9092`: comunicação interna entre containers Docker.

Criar o tópico principal:

```powershell
docker exec enade-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic enade-questoes --partitions 3 --replication-factor 1
```

Criar a Dead Letter Queue:

```powershell
docker exec enade-kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --if-not-exists --topic enade-questoes-dlq --partitions 3 --replication-factor 1
```

Ambos os tópicos possuem três partições e fator de replicação 1, adequado ao ambiente local com um único broker.

O produtor utiliza o identificador da questão como chave da mensagem. Assim, mensagens com o mesmo ID são direcionadas à mesma partição, mantendo-se a configuração de particionamento.

### 3.1. Criar o índice Elasticsearch

O Elasticsearch utiliza o índice `enade-questoes` para armazenar as questões validadas pelo consumidor Kafka.

O mapping está definido em:

`docs/elasticsearch/indice-questoes.json`

Ele configura os tipos dos campos, os filtros estruturados e o analisador `brazilian` para buscas textuais em português.

Após iniciar a infraestrutura e instalar as dependências Python, execute no PowerShell:

```powershell
@'
import json
from pathlib import Path
from elasticsearch import Elasticsearch

cliente = Elasticsearch("http://localhost:9200")
indice = "enade-questoes"

try:
    if cliente.indices.exists(index=indice):
        print("Indice ja existe:", indice)
    else:
        caminho = Path("docs/elasticsearch/indice-questoes.json")
        configuracao = json.loads(caminho.read_text(encoding="utf-8"))

        cliente.indices.create(
            index=indice,
            **configuracao,
        )
        print("Indice criado:", indice)
finally:
    cliente.close()
'@ | .\.venv\Scripts\python.exe -
```

O comando cria o índice somente quando ele ainda não existe, evitando erros em execuções posteriores.

Para verificar a quantidade de documentos armazenados:

```powershell
Invoke-RestMethod -Uri "http://localhost:9200/enade-questoes/_count"
```

**Importante:** o índice deve existir antes da execução do consumidor, pois seu mapping define a estrutura e os analisadores utilizados nas pesquisas.

### 4. Publicar uma questão

Executar o produtor:

```powershell
.\.venv\Scripts\python.exe .\producer\publicar_questao.py
```

O produtor publica o documento disponível em:

`docs/exemplos/questao-objetiva.json`

Os logs informam o identificador da questão, o tópico, a partição e o offset.

### 5. Executar o consumidor

```powershell
.\.venv\Scripts\python.exe .\consumer\consumir_questoes.py
```


O consumidor:

1. Recebe as mensagens do tópico principal `enade-questoes`.
2. Verifica a codificação e a estrutura JSON.
3. Valida o JSON Schema e as regras semânticas.
4. Encaminha mensagens inválidas à DLQ e confirma seus offsets somente após o envio bem-sucedido.
5. Indexa as questões válidas no Elasticsearch, utilizando o ID da questão como identificador do documento.
6. Atualiza o documento existente quando uma questão com o mesmo ID é reprocessada.
7. Confirma o offset de uma questão válida somente após a indexação bem-sucedida.
8. Preserva o offset pendente caso a indexação falhe, permitindo o reprocessamento.


O consumidor pertence ao grupo `enade-validacao` e encerra a execução após aproximadamente 30 segundos sem novas mensagens.

### 6. Consultar os offsets

```powershell
docker exec enade-kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group enade-validacao
```

Informações importantes:

- `CURRENT-OFFSET`: próxima posição confirmada pelo grupo.
- `LOG-END-OFFSET`: posição final disponível no tópico.
- `LAG`: quantidade de mensagens pendentes.

Um `LAG` igual a zero indica que, naquele momento, o grupo não possui mensagens pendentes na partição.

### 7. Consultar questões no Elasticsearch

As consultas estão implementadas no módulo `consumer/consultas.py`.

A função `buscar_questoes()` permite pesquisar questões pelo enunciado, aplicando filtros opcionais por ano, curso e tipo de questão.

A função `agregar_questoes()` retorna estatísticas agrupadas por ano, curso e tipo.

Para executar um exemplo de busca e agregação, utilize o PowerShell na raiz do repositório:

```powershell
@'
from elasticsearch import Elasticsearch
from consumer.consultas import buscar_questoes, agregar_questoes

cliente = Elasticsearch("http://localhost:9200")

try:
    resposta = buscar_questoes(
        cliente,
        "bancos",
        ano=2023,
        tipo_questao="objetiva",
    )

    print("Questoes encontradas:", resposta["hits"]["total"]["value"])

    for questao in resposta["hits"]["hits"]:
        print("ID:", questao["_id"])
        print("Pontuacao:", questao["_score"])
        print("Highlight:", questao.get("highlight", {}))

    estatisticas = agregar_questoes(cliente)

    for nome in ("por_ano", "por_curso", "por_tipo"):
        print("\nAgregacao:", nome)

        for grupo in estatisticas["aggregations"][nome]["buckets"]:
            print(grupo["key"], ":", grupo["doc_count"])
finally:
    cliente.close()
'@ | .\.venv\Scripts\python.exe -
```

O Elasticsearch calcula a relevância textual por meio do campo `_score`.

O highlight destaca os termos encontrados utilizando marcações `<em>`.

As agregações utilizam os campos estruturados do índice para produzir contagens por categoria.

Os resultados dependem dos documentos já indexados.

## Confiabilidade e tratamento de falhas

### Dead Letter Queue (DLQ)

Mensagens com JSON malformado ou documentos rejeitados pela validação são encaminhados ao tópico `enade-questoes-dlq`.

O registro enviado à DLQ contém:

- Tópico de origem.
- Partição de origem.
- Offset de origem.
- Motivo da rejeição.
- Conteúdo original codificado em Base64.

O offset da mensagem original é confirmado somente após o envio bem-sucedido à DLQ.

Se o envio falhar, a exceção é propagada, preservando a possibilidade de reprocessamento.

### Idempotência e persistência no Elasticsearch

Na Issue #48, foi desenvolvido um mecanismo de deduplicação local
utilizando SQLite, implementado em `consumer/idempotencia.py`.

Esse módulo permanece no repositório como parte do histórico
de desenvolvimento, mas não é utilizado pelo consumidor atual.

A partir da Issue #49, as questões válidas são persistidas
diretamente no índice `enade-questoes` do Elasticsearch.

A função `indexar_questao()`, implementada em
`consumer/indexacao.py`, utiliza o campo `id` da questão
como identificador do documento (`_id`).

Esse mecanismo permite:

- Criar um documento quando o identificador ainda não existe.
- Atualizar o documento existente quando o mesmo ID é reprocessado.
- Evitar a criação de múltiplos documentos com o mesmo identificador.
- Reprocessar mensagens após falhas sem duplicar documentos no índice.

O consumidor confirma o offset do Kafka somente após a operação
de indexação ser concluída com sucesso.

Se a indexação falhar, a exceção é propagada e o offset não é
confirmado, permitindo uma nova tentativa de processamento.

**Limitação importante:** Kafka e Elasticsearch não participam de
uma transação distribuída. Portanto, se o processo falhar após a
indexação, mas antes da confirmação do offset, a mensagem poderá
ser processada novamente.

O uso de IDs determinísticos impede a criação de documentos
duplicados nesse cenário, mas uma nova indexação pode atualizar
o documento existente.

O mecanismo foi validado com testes automatizados e com uma
simulação controlada de falha utilizando Kafka e Elasticsearch reais.

### Controle de offsets

O consumidor utiliza:

`enable_auto_commit=False`

A função `confirmar_mensagem()` confirma explicitamente o offset seguinte ao da mensagem processada, na partição correspondente.

O procedimento evita confirmar indiscriminadamente as posições atuais de todas as partições do consumidor.

### Recuperação de falhas

A recuperação de falhas foi validada com o Kafka real em dois cenários.

**Cenário 1 — Falha no envio à DLQ**

1. Uma mensagem inválida foi publicada no Kafka.
2. Foi simulada uma falha no envio à DLQ.
3. O consumidor encerrou sem confirmar o offset.
4. O Kafka manteve a mensagem pendente, com `LAG = 1`.
5. O consumidor foi executado novamente.
6. A mensagem foi encaminhada à DLQ com sucesso.
7. O offset avançou e o `LAG` retornou a zero.

**Cenário 2 — Falha na indexação do Elasticsearch**

1. Uma questão válida foi publicada no tópico `enade-questoes`.
2. Foi simulada uma falha durante a indexação.
3. O consumidor propagou a exceção e encerrou suas conexões.
4. O Kafka preservou a mensagem na partição 2, offset 8.
5. O grupo `enade-validacao` permaneceu com `CURRENT-OFFSET = 8` e `LAG = 1`.
6. O consumidor foi executado novamente, sem a falha simulada.
7. A questão foi indexada com sucesso no Elasticsearch.
8. O Kafka confirmou o próximo offset (`9`).
9. O `LAG` retornou a zero.
10. O índice permaneceu com apenas um documento, sem duplicação.

Esses testes demonstram que o consumidor permite o reprocessamento
de mensagens após falhas controladas e reinicialização manual.

A indexação utiliza o ID da questão como identificador do documento
no Elasticsearch, permitindo atualizar um registro existente quando
uma mensagem é processada novamente.

**Limitações:** não há reinicialização automática do consumidor nem
transação distribuída entre Kafka e Elasticsearch. Uma mensagem pode
ser reprocessada caso ocorra falha após a indexação e antes da
confirmação do offset.

## Logs

Produtor e consumidor utilizam o módulo `logging` do Python.

Os registros contêm:

- Data e horário.
- Nível de severidade.
- Origem do evento.
- Informações da mensagem e do processamento.

Principais níveis:

- `INFO`: publicação de questões, indexação no Elasticsearch, confirmação do processamento e encerramento de conexões.
- `WARNING`: mensagens com JSON malformado ou questões rejeitadas pela validação.
- `ERROR`: falhas de indexação ou outras falhas de processamento, com informações para diagnóstico.

Os logs de indexação incluem:

- Identificador da questão.
- Resultado da operação no Elasticsearch (`created` ou `updated`).
- Partição Kafka de origem.
- Offset da mensagem.

Quando ocorre uma falha na indexação, o consumidor registra o erro e
propaga a exceção sem confirmar o offset da mensagem.

As mensagens informativas internas da biblioteca Kafka são reduzidas
para facilitar a análise dos logs da aplicação.

## Testes

### Testes automatizados do Kafka

Executar:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_consumer_kafka.py" -v
```

Cenários cobertos:

1. Confirmação individual de offsets.
2. Propagação de falhas durante o commit.
3. Falha da DLQ com JSON malformado.
4. Falha da DLQ com questão rejeitada pelo schema.
5. Reprocessamento após falha temporária no envio à DLQ.
6. Falha na indexação Elasticsearch sem confirmação do offset.
7. Indexação bem-sucedida com confirmação do offset seguinte.

**Resultado: 7 testes do consumidor Kafka aprovados.**

### Testes automatizados das consultas Elasticsearch

Executar:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_consultas_elasticsearch.py" -v
```


Cenários cobertos:

1. Busca textual com highlight.
2. Busca com filtros combinados.
3. Agregações por ano, curso e tipo de questão.

**Resultado: 3 testes de consultas aprovados.**

### Executar todos os testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**Resultado da validação em 18/11/2026: 10 testes executados, 10 aprovados.**

Também foram realizados testes funcionais com Kafka e Elasticsearch reais,
incluindo indexação, consultas, filtros, agregações, prevenção de documentos
duplicados por ID e recuperação após falhas controladas.


### Validação do modelo ENADE

Para executar o validador de documentos:

```powershell
.\.venv\Scripts\python.exe .\scripts\validar_modelo.py
```

O validador verifica os exemplos, o JSON Schema e as regras semânticas aplicáveis.

## Segurança

Credenciais e arquivos sensíveis não devem ser versionados.

Utilize o arquivo `.env.example` como referência para configurações locais.

A configuração atual do Kafka utiliza comunicação PLAINTEXT em ambiente de desenvolvimento. Não deve ser exposta diretamente à internet.

Autenticação, autorização e comunicação segura entre os serviços deverão ser incorporadas conforme a evolução da arquitetura.

## Documentação

A documentação técnica do projeto é mantida na pasta `docs/`.

### Modelo de dados

- [Modelo estruturado de questão ENADE](docs/modelo-questao.md)
- [JSON Schema](docs/schemas/questao.schema.json)
- [Exemplo de questão objetiva](docs/exemplos/questao-objetiva.json)
- [Exemplo de questão discursiva](docs/exemplos/questao-discursiva.json)

## Próximos passos

- Issue #49: integração com Elasticsearch.
- Persistência definitiva das questões estruturadas.
- Garantia de idempotência no destino.
- Integração com API e mecanismos de consulta.
- Ampliação das funcionalidades de segurança e observabilidade.

## Disciplina

Projeto desenvolvido para a disciplina de Big Data do curso de Sistemas de Informação.
