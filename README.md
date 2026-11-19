
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
│   ├── catalogo.json
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

A idempotência de ponta a ponta, incluindo a persistência definitiva no Elasticsearch, ainda depende da Issue #49.

## Funcionalidades planejadas

- Extração de questões de provas do ENADE.
- Segmentação de cada questão em documentos independentes.
- Tratamento de fórmulas, diagramas, tabelas e imagens.
- Indexação no Elasticsearch.
- Busca full-text em português.
- Filtros por curso, área, ano, tipo e competência.
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

1. Recebe as mensagens do tópico principal.
2. Verifica a codificação e a estrutura JSON.
3. Valida o schema e as regras semânticas.
4. Encaminha mensagens inválidas à DLQ.
5. Identifica questões repetidas no SQLite.
6. Confirma individualmente os offsets das mensagens tratadas.

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

## Confiabilidade e tratamento de falhas

### Dead Letter Queue (DLQ)

Mensagens com payload ausente (`value=None`), JSON malformado ou documentos rejeitados pela validação são encaminhados ao tópico `enade-questoes-dlq`.

O registro enviado à DLQ contém:

- Tópico de origem.
- Partição de origem.
- Offset de origem.
- Motivo da rejeição.
- Conteúdo original codificado em Base64 (`null` quando o payload está ausente e `""` quando o payload é vazio `b""`).

O offset da mensagem original é confirmado somente após o envio bem-sucedido à DLQ.

Se o envio falhar, a exceção é propagada, preservando a possibilidade de reprocessamento.

### Deduplicação local

O arquivo `consumer/idempotencia.py` utiliza SQLite para registrar os identificadores das questões.

Banco local:

`data/processed/idempotencia.sqlite3`

O banco é persistente entre execuções e está excluído do versionamento pelo `.gitignore`.

Uma questão com ID já registrado é reconhecida como duplicada.

**Limitação importante:** atualmente, o ID é registrado no SQLite antes de existir uma gravação definitiva no Elasticsearch. Portanto, o mecanismo demonstra a deduplicação local, mas ainda não garante idempotência de ponta a ponta.

A Issue #49 deverá tratar a consistência entre gravação no Elasticsearch, controle de duplicações e confirmação dos offsets.

### Controle de offsets

O consumidor utiliza:

`enable_auto_commit=False`

A função `confirmar_mensagem()` confirma explicitamente o offset seguinte ao da mensagem processada, na partição correspondente.

O procedimento evita confirmar indiscriminadamente as posições atuais de todas as partições do consumidor.

### Recuperação de falhas

A recuperação foi testada com o Kafka real.

Cenário validado:

1. Uma mensagem inválida foi publicada no Kafka.
2. Foi simulada uma falha no envio à DLQ.
3. O consumidor encerrou sem confirmar o offset.
4. O Kafka manteve a mensagem pendente, com `LAG = 1`.
5. O consumidor foi executado novamente.
6. A mensagem foi encaminhada à DLQ com sucesso.
7. O offset avançou e o `LAG` retornou a zero.

Esse teste comprova a retomada do processamento após uma falha controlada e reinicialização manual do consumidor.

Não há, nesta etapa, garantia de reinicialização automática do processo nem de transação distribuída entre Kafka, SQLite e Elasticsearch.

## Logs

Produtor e consumidor utilizam o módulo `logging` do Python.

Os registros contêm:

- Data e horário.
- Nível de severidade.
- Origem do evento.
- Informações da mensagem e do processamento.

Principais níveis:

- `INFO`: publicação, consumo, duplicação e encerramento de conexões.
- `WARNING`: mensagens inválidas ou rejeitadas.
- `ERROR`: falhas de publicação, envio à DLQ, confirmação de offsets, processamento ou fechamento de recursos, com detalhes para diagnóstico.

As mensagens informativas internas da biblioteca Kafka são reduzidas para facilitar a análise dos logs da aplicação.

## Testes

### Testes automatizados do Kafka

Executar:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_consumer_kafka.py" -v
```

Cenários cobertos:

1. Confirmação individual de offsets.
2. Propagação e registro de falhas durante o commit.
3. Falha da DLQ com JSON malformado.
4. Falha da DLQ com questão rejeitada pelo schema.
5. Reprocessamento após falha temporária simulada.
6. Mensagem com payload ausente (`value=None`) encaminhada à DLQ e proteção contra falha da DLQ.
7. Diferenciação na DLQ entre payload ausente (`None`) e payload vazio (`b""`).
8. Fluxo válido do consumidor, deduplicação local no SQLite e rejeição semântica encaminhada à DLQ.
9. Fechamento seguro de recursos no consumidor preservando a exceção original.
10. Validação do campo `id` e tratamento de erros no produtor.

Resultado da validação realizada em 18/11/2026:

**17 testes executados, 17 aprovados.**

Também foram realizados testes funcionais com Kafka real para publicação, consumo, DLQ, deduplicação e recuperação de falhas.

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

## Acervo de documentos do ENADE

Os arquivos brutos utilizados pelo projeto são obtidos do portal oficial do Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep).

O acervo é organizado por ano e curso, permitindo identificar os documentos utilizados na extração e garantir a rastreabilidade das questões até sua fonte original.

### Estrutura de armazenamento

```text
data/
├── catalogo.json
└── raw/
    └── enade/
        ├── 2021/
        │   └── sistemas_de_informacao/
        │       ├── enade_2021_sistemas_de_informacao_prova.pdf
        │       └── enade_2021_sistemas_de_informacao_gabarito.pdf
        └── 2023/
            └── sistemas_de_informacao/
```

A estrutura pode ser ampliada conforme novos cursos e edições forem adicionados. Diretórios ainda sem documentos são mantidos com arquivos `.gitkeep`.

### Padrão de nomenclatura

Os arquivos seguem o padrão:

`enade_<ano>_<curso>_<tipo>.pdf`

Exemplos:

- `enade_2021_sistemas_de_informacao_prova.pdf`
- `enade_2021_sistemas_de_informacao_gabarito.pdf`

### Origem e obtenção dos documentos

Os documentos devem ser obtidos de fontes oficiais do Inep:

- [Provas e gabaritos do ENADE 2021](https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enade/provas-e-gabaritos/2021)
- [Provas e gabaritos do ENADE 2023](https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enade/provas-e-gabaritos/2023)

Para recuperar os arquivos, consulte o campo `origem` no arquivo `data/catalogo.json`, baixe cada PDF e salve-o no caminho indicado pelo campo `caminho`.

O catálogo é a referência para identificar quais documentos pertencem ao acervo do projeto.

### Catálogo dos documentos

O arquivo `data/catalogo.json` registra:

- Ano da edição.
- Curso.
- Tipo do documento.
- Nome padronizado do arquivo.
- Caminho relativo no repositório.
- URL oficial de origem.

Essas informações permitirão que o pipeline de extração identifique o PDF de origem de cada questão.

### Controle de versionamento

Os PDFs brutos armazenados em `data/raw/` são ignorados pelo Git para evitar o versionamento de arquivos grandes.

São versionados somente a estrutura de diretórios, os arquivos `.gitkeep`, o catálogo JSON e a documentação.

Os PDFs precisam ser baixados novamente ao clonar o repositório, seguindo as URLs e os caminhos registrados no catálogo.

Nesta etapa, não é realizada a extração nem a segmentação das questões.

## Próximos passos

- Issue #49: integração com Elasticsearch.
- Persistência definitiva das questões estruturadas.
- Garantia de idempotência no destino.
- Integração com API e mecanismos de consulta.
- Ampliação das funcionalidades de segurança e observabilidade.

## Disciplina

Projeto desenvolvido para a disciplina de Big Data do curso de Sistemas de Informação.
