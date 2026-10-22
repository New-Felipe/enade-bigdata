# ENADE Big Data

Plataforma distribuída para processamento, indexação e busca sobre o acervo histórico de provas do ENADE.

O projeto tem como objetivo transformar provas em PDF em documentos estruturados e pesquisáveis, utilizando processamento distribuído, mensageria, indexação full-text, cache e autenticação com perfis de acesso.

## Arquitetura prevista

Fluxo principal:

PDFs → Extração e Estruturação → Apache Kafka → Elasticsearch → API / Redis → Cliente Web

Camada transversal de segurança:

- LDAP para autenticação de usuários e perfis de acesso
- Kerberos para autenticação entre serviços

## Tecnologias previstas

- Python
- Apache Kafka
- Elasticsearch
- Redis
- Docker / Docker Compose
- LDAP
- Kerberos
- FastAPI
- Frontend web a definir

## Estrutura inicial

```text
.
├── api/
├── consumer/
├── data/
│   ├── processed/
│   └── raw/
├── docs/
├── extractor/
├── frontend/
├── producer/
├── security/
│   ├── kerberos/
│   └── ldap/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Funcionalidades planejadas

- Extração de questões de provas do ENADE
- Segmentação de cada questão em documentos independentes
- Tratamento de fórmulas, diagramas, tabelas e imagens
- Publicação de documentos via Kafka
- Indexação no Elasticsearch
- Busca full-text em português
- Filtros por curso, área, ano, tipo e competência
- Cache de consultas com Redis
- Sessão e lista de questões
- Perfis de acesso para Estudante e Professor
- Exportação de questões em PDF ou JSON
- Tratamento de mensagens inválidas com DLQ
- Idempotência e tolerância a falhas

## Status

Projeto em fase inicial de configuração da arquitetura e infraestrutura.

## Execução

A execução completa do ambiente será disponibilizada por Docker Compose.

```bash
docker compose up -d
```

> Esta seção será atualizada conforme os serviços forem implementados.

## Segurança

Credenciais e arquivos sensíveis não devem ser versionados.

Utilize o arquivo `.env.example` como referência para configuração local.

## Documentação

A documentação técnica do projeto será mantida na pasta `docs/`.

## Disciplina

Projeto desenvolvido para a disciplina de Big Data do curso de Sistemas de Informação.