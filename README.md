# BioéticaRAG

**Assistente inteligente para triagem ética preliminar de projetos de pesquisa**

Powered by **Claude (Anthropic)** + **LangChain** + **Chroma DB** + **Streamlit**

---

## Opção A — Rodar com Docker (recomendado)

### Pré-requisitos
- Docker + Docker Compose instalados
- Chaves de API configuradas

### 1. Configurar as chaves de API

```bash
cp .env.example .env
# edite .env com suas chaves
```

### 2. Adicionar os PDFs das normas

```
docs/
├── CNS_466_2012.pdf
├── CNS_510_2016.pdf
├── CNS_441_2011.pdf
├── CNS_340_2004.pdf
├── CNS_580_2018.pdf
└── LGPD_Lei_13709_2018.pdf
```

### 3. Subir tudo

```bash
docker compose up --build
```

O que acontece automaticamente:
1. A imagem é construída com todas as dependências
2. O serviço `setup` verifica se `chroma_db/` está vazio e indexa os PDFs se necessário
3. O serviço `app` sobe o Streamlit assim que o setup termina

Acesse: **http://localhost:8501**

### Comandos úteis

```bash
# Subir em background
docker compose up --build -d

# Ver logs em tempo real
docker compose logs -f app

# Forçar reindexação dos documentos
docker compose run --rm -e FORCE_REINDEX=1 setup

# Parar tudo
docker compose down

# Parar e remover volumes (apaga chroma_db)
docker compose down -v
```

---

## Opção B — Rodar sem Docker (local)

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar as chaves de API

```bash
cp .env.example .env
# edite .env com suas chaves
```

### 3. Indexar os documentos (uma vez)

```bash
python setup_rag.py
```

### 4. Iniciar o app

```bash
streamlit run app.py
```

---

## Estrutura

```
bioetica_rag/
├── app.py              ← Interface Streamlit
├── rag_engine.py       ← Motor RAG: retriever, prompts, funções
├── setup_rag.py        ← Indexação dos PDFs
├── Dockerfile          ← Imagem Docker
├── docker-compose.yml  ← Orquestração dos serviços
├── .dockerignore       ← Arquivos ignorados na imagem
├── requirements.txt    ← Dependências Python
├── .env.example        ← Template das variáveis de ambiente
├── docs/               ← Coloque os PDFs aqui
└── chroma_db/          ← Criado automaticamente pelo setup
```

---

## Por que duas chaves de API?

| Chave | Para quê | Modelo usado |
|---|---|---|
| `ANTHROPIC_API_KEY` | Geração de texto (LLM) | `claude-sonnet-4-5` |
| `OPENAI_API_KEY` | Embeddings (vetorização) | `text-embedding-3-small` |

O Claude não oferece API de embeddings. O `text-embedding-3-small` da OpenAI
é o modelo mais barato disponível (~$0.02/1M tokens) — a indexação completa
custa menos de $0.01.

---

## Custo estimado de API

| Operação | Tokens aprox. | Custo Claude Sonnet |
|---|---|---|
| Análise completa | ~3.000 | ~$0.015 |
| Consulta livre | ~1.500 | ~$0.008 |
| Checklist | ~1.200 | ~$0.006 |
| Indexação (uma vez) | ~500k embed | ~$0.01 (OpenAI) |

---

## Migração do Open WebUI

- **System prompts** → substitua `PROMPT_ANALISE`, `PROMPT_CONSULTA` e `PROMPT_CHECKLIST` em `rag_engine.py`
- **Casos de teste** → adicione no dicionário `CASOS` em `app.py`
- **Coleção RAG existente** → aponte `CHROMA_DIR` em `rag_engine.py` para o diretório existente

---

## Limitações

- Não substitui avaliação formal pelo CEP/CONEP
- Não constitui parecer jurídico definitivo
- A qualidade depende dos documentos indexados
- Casos complexos requerem análise presencial com especialista
