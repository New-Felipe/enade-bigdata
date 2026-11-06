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

## Disciplina

Projeto desenvolvido para a disciplina de Big Data do curso de Sistemas de Informação.