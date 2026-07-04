"""
setup_rag.py
============
Executa UMA VEZ para indexar os PDFs da pasta docs/ no banco vetorial Chroma.

Uso:
    python setup_rag.py

Pré-requisitos:
    1. pip install -r requirements.txt
    2. Copiar .env.example para .env e preencher as chaves
    3. Colocar os PDFs das normas dentro da pasta docs/
"""

import os
import sys
import shutil
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
BASE_DIR   = Path(__file__).parent
DOCS_DIR   = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"

# ---------------------------------------------------------------------------
# Verificações
# ---------------------------------------------------------------------------

def checar_dependencias():
    pacotes = ["langchain", "chromadb", "pypdf", "langchain_openai"]
    faltando = []
    for p in pacotes:
        try:
            __import__(p)
        except ImportError:
            faltando.append(p)
    if faltando:
        print(f"❌  Dependências ausentes: {', '.join(faltando)}")
        print("    Execute: pip install -r requirements.txt")
        sys.exit(1)


def checar_docs():
    pdfs = list(DOCS_DIR.glob("*.pdf"))
    if not DOCS_DIR.exists() or not pdfs:
        print(f"❌  Nenhum PDF encontrado em: {DOCS_DIR}")
        print("\n    Crie a pasta docs/ e adicione os arquivos abaixo:")
        normas = [
            "CNS_466_2012.pdf",
            "CNS_510_2016.pdf",
            "CNS_441_2011.pdf",
            "CNS_340_2004.pdf",
            "CNS_580_2018.pdf",
            "LGPD_Lei_13709_2018.pdf",
        ]
        for n in normas:
            print(f"    • {n}")
        print("\n    Fontes:")
        print("    • Resoluções CNS: https://conselho.saude.gov.br/resolucoes")
        print("    • LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm")
        sys.exit(1)
    return pdfs


def checar_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌  OPENAI_API_KEY não encontrada no arquivo .env")
        print("    Os embeddings usam o modelo text-embedding-3-small da OpenAI.")
        print("    Configure a chave em .env antes de continuar.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Indexação
# ---------------------------------------------------------------------------

def indexar():
    from langchain_community.document_loaders import PyPDFDirectoryLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings

    # --- Carregar PDFs ---
    print(f"\n📂  Carregando PDFs de: {DOCS_DIR}")
    loader = PyPDFDirectoryLoader(str(DOCS_DIR))
    documentos = loader.load()

    if not documentos:
        print("❌  Nenhum conteúdo extraído dos PDFs. Verifique se os arquivos não estão protegidos.")
        sys.exit(1)

    print(f"    ✓ {len(documentos)} página(s) carregada(s)")

    # --- Dividir em chunks ---
    print("\n✂️   Dividindo em chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,       # ~800 tokens por chunk
        chunk_overlap=100,    # sobreposição para não perder contexto entre chunks
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documentos)
    print(f"    ✓ {len(chunks)} chunk(s) criado(s)")

    # --- Embeddings ---
    print("\n🔢  Gerando embeddings com text-embedding-3-small...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # --- Persistir no Chroma em lotes de 100 ---
    print("💾  Persistindo no Chroma DB...")
    LOTE = 100
    vectordb = None
    for i in range(0, len(chunks), LOTE):
        lote = chunks[i : i + LOTE]
        fim  = min(i + LOTE, len(chunks))
        print(f"    Chunk {i+1}–{fim} de {len(chunks)}...", end="\r")
        if vectordb is None:
            vectordb = Chroma.from_documents(
                lote,
                embeddings,
                persist_directory=str(CHROMA_DIR),
            )
        else:
            vectordb.add_documents(lote)

    print(f"\n    ✓ {len(chunks)} chunks gravados em: {CHROMA_DIR}")
    print("\n🚀  Pronto! Agora execute: streamlit run app.py\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 55)
    print("  BioéticaRAG — Indexação da base documental")
    print("=" * 55)

    checar_dependencias()
    pdfs = checar_docs()
    checar_api_key()

    print(f"\n    PDFs encontrados: {len(pdfs)}")
    for p in pdfs:
        print(f"    • {p.name}")

    # Se banco já existir, perguntar se recria
    # Em modo não-interativo (Docker / CI), usa a variável FORCE_REINDEX=1
    if CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir()):
        force = os.getenv("FORCE_REINDEX", "").lower() in ("1", "true", "yes")
        if not force:
            # Tenta ler do terminal; se não houver TTY (Docker), cancela automaticamente
            if sys.stdin.isatty():
                resp = input("\n⚠️   Banco vetorial já existe. Recriar do zero? (s/N): ").strip().lower()
                force = (resp == "s")
            else:
                print("⚠️   Banco vetorial já existe e FORCE_REINDEX não está ativo. Pulando.")
                sys.exit(0)
        if force:
            shutil.rmtree(CHROMA_DIR)
            print("    Banco anterior removido.\n")
        else:
            print("Operação cancelada. O banco existente será mantido.")
            sys.exit(0)

    indexar()
