"""
rag_engine.py
=============
Motor RAG do BioéticaRAG.

Responsabilidades:
  • Carregar o banco vetorial Chroma (criado pelo setup_rag.py)
  • Recuperar trechos normativos relevantes para cada consulta
  • Chamar Claude (claude-sonnet-4-5) com os trechos como contexto
  • Expor três funções públicas:
      - analisar_projeto(descricao)  → dict com seções da análise
      - consulta_livre(pergunta)     → (resposta, lista_de_fontes)
      - gerar_checklist(descricao)   → dict com critérios éticos
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# LLM: Claude via LangChain-Anthropic
# ---------------------------------------------------------------------------
from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

CHROMA_DIR = Path(__file__).parent / "chroma_db"

# Claude Sonnet — boa relação custo/qualidade para raciocínio jurídico-normativo
llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=2048,
    temperature=0.1,  # baixa temperatura para respostas mais precisas e consistentes
)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Cache do vectordb para não reabrir a cada chamada
_vectordb = None


def _get_retriever(k: int = 6):
    """Retorna o retriever Chroma. Carrega o banco na primeira chamada."""
    global _vectordb
    if _vectordb is None:
        _vectordb = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings,
        )
    return _vectordb.as_retriever(search_kwargs={"k": k})


def _formatar_docs(docs) -> str:
    """Converte lista de Documents em texto com identificação da fonte."""
    trechos = []
    for doc in docs:
        fonte = doc.metadata.get("source", "norma desconhecida")
        # Mostra só o nome do arquivo, sem o caminho completo
        fonte = Path(fonte).name if fonte else "norma"
        trechos.append(f"[{fonte}]\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(trechos)


# ---------------------------------------------------------------------------
# Prompts especializados
# ---------------------------------------------------------------------------

PROMPT_ANALISE = PromptTemplate.from_template("""
Você é um especialista sênior em ética em pesquisa no Brasil, com amplo conhecimento do
sistema CEP/CONEP, das resoluções do Conselho Nacional de Saúde e da LGPD.

Use os trechos normativos recuperados abaixo como referência principal.
Cite as normas pelos nomes quando relevante (ex: "conforme a Resolução CNS 466/2012, art. X").

════════════ TRECHOS NORMATIVOS RECUPERADOS ════════════
{context}
════════════════════════════════════════════════════════

PROJETO DESCRITO PELO PESQUISADOR:
{projeto}

Produza uma análise ética preliminar estruturada com exatamente estas seções
(use os títulos abaixo como estão escritos):

## Resumo do projeto
Síntese em 2–3 frases do que o projeto propõe e com quem/o quê trabalha.

## Normas aplicáveis
Liste as resoluções, leis e regulamentos que incidem sobre este projeto. Justifique brevemente cada um.

## Necessidade de submissão ao CEP e/ou CONEP
Responda com clareza: precisa de CEP? Precisa de CONEP? Por quê?
Indique se o projeto pode se enquadrar em dispensa de apreciação ética (Res. 510/2016, art. 1º).

## Requisitos éticos identificados
Liste os requisitos que o projeto deve cumprir antes de iniciar.

## Implicações LGPD e dados sensíveis
Analise se há dados pessoais ou dados sensíveis (conforme art. 5º da LGPD).
Indique base legal adequada para o tratamento e obrigações aplicáveis.

## Necessidade de TCLE
O projeto exige TCLE? Para quem? Existe necessidade de TALE (assentimento)?
Há situação de dispensa de TCLE? Justifique com base nas normas.

## Possíveis riscos regulatórios
Liste riscos de não conformidade identificados a partir da descrição fornecida.

## Limitações desta análise
Explique o que esta triagem preliminar não cobre e o que o pesquisador deve verificar formalmente.
""")

PROMPT_CONSULTA = PromptTemplate.from_template("""
Você é um especialista em ética em pesquisa no Brasil, com profundo conhecimento das
resoluções do CNS, do sistema CEP/CONEP, da LGPD e da Plataforma Brasil.

Use os trechos normativos abaixo como base para sua resposta.
Cite a norma e o artigo sempre que possível.

════════════ TRECHOS NORMATIVOS RECUPERADOS ════════════
{context}
════════════════════════════════════════════════════════

PERGUNTA:
{pergunta}

Responda de forma clara e objetiva. Se a pergunta envolver distinções ou definições,
estruture com marcadores. Se não for possível responder com base nos documentos disponíveis,
informe isso claramente e oriente onde encontrar a informação oficial.
""")

PROMPT_CHECKLIST = PromptTemplate.from_template("""
Você é um especialista em ética em pesquisa no Brasil.

Use os trechos normativos abaixo para embasar sua avaliação.

════════════ TRECHOS NORMATIVOS RECUPERADOS ════════════
{context}
════════════════════════════════════════════════════════

PROJETO:
{projeto}

Avalie o projeto e responda SOMENTE com um JSON válido, sem markdown, sem texto fora do JSON.
Cada campo deve ter exatamente um dos valores: "Sim", "Não" ou "Indeterminado".

{{
  "seres_humanos":       "...",
  "dados_sensiveis":     "...",
  "material_biologico":  "...",
  "dados_geneticos":     "...",
  "populacoes_vulneraveis": "...",
  "tcle":                "...",
  "cep":                 "...",
  "conep":               "...",
  "observacoes": "Parágrafo curto explicando os principais critérios identificados e incertezas."
}}
""")


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def analisar_projeto(descricao: str) -> dict:
    """
    Analisa eticamente um projeto de pesquisa.

    Parâmetros:
        descricao: texto livre descrevendo o projeto

    Retorna:
        dict com chaves: resumo, normas, cep_conep, requisitos_eticos,
                         lgpd, tcle, riscos, limitacoes
    """
    retriever = _get_retriever(k=7)
    docs = retriever.invoke(descricao)
    contexto = _formatar_docs(docs)

    chain = PROMPT_ANALISE | llm | StrOutputParser()
    texto = chain.invoke({"context": contexto, "projeto": descricao})

    return _parsear_secoes_analise(texto)


def consulta_livre(pergunta: str) -> tuple[str, list[dict]]:
    """
    Responde perguntas livres sobre a base normativa.

    Retorna:
        (resposta: str, fontes: list[{"source": str, "content": str}])
    """
    retriever = _get_retriever(k=5)
    docs = retriever.invoke(pergunta)
    contexto = _formatar_docs(docs)

    chain = PROMPT_CONSULTA | llm | StrOutputParser()
    resposta = chain.invoke({"context": contexto, "pergunta": pergunta})

    fontes = [
        {
            "source": Path(doc.metadata.get("source", "norma")).name,
            "content": doc.page_content.strip()[:500],
        }
        for doc in docs
    ]
    return resposta, fontes


def gerar_checklist(descricao: str) -> dict:
    """
    Gera checklist ético automático para um projeto.

    Retorna:
        dict com os critérios e seus resultados (Sim / Não / Indeterminado)
    """
    retriever = _get_retriever(k=5)
    docs = retriever.invoke(descricao)
    contexto = _formatar_docs(docs)

    chain = PROMPT_CHECKLIST | llm | StrOutputParser()
    texto = chain.invoke({"context": contexto, "projeto": descricao})

    # Limpar possíveis marcações de bloco de código antes de parsear
    texto_limpo = (
        texto.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )

    try:
        return json.loads(texto_limpo)
    except json.JSONDecodeError:
        # Fallback seguro se o modelo não retornar JSON válido
        return {
            "seres_humanos": "Indeterminado",
            "dados_sensiveis": "Indeterminado",
            "material_biologico": "Indeterminado",
            "dados_geneticos": "Indeterminado",
            "populacoes_vulneraveis": "Indeterminado",
            "tcle": "Indeterminado",
            "cep": "Indeterminado",
            "conep": "Indeterminado",
            "observacoes": "Não foi possível interpretar a resposta. Tente novamente.",
        }


# ---------------------------------------------------------------------------
# Parser interno
# ---------------------------------------------------------------------------

def _parsear_secoes_analise(texto: str) -> dict:
    """
    Transforma o texto markdown gerado pelo Claude em um dicionário
    com uma chave por seção.
    """
    SECOES = {
        "## Resumo do projeto":                        "resumo",
        "## Normas aplicáveis":                        "normas",
        "## Necessidade de submissão ao CEP e/ou CONEP": "cep_conep",
        "## Requisitos éticos identificados":          "requisitos_eticos",
        "## Implicações LGPD e dados sensíveis":       "lgpd",
        "## Necessidade de TCLE":                      "tcle",
        "## Possíveis riscos regulatórios":            "riscos",
        "## Limitações desta análise":                 "limitacoes",
    }

    resultado = {}
    titulos = list(SECOES.keys())

    for i, titulo in enumerate(titulos):
        pos_inicio = texto.find(titulo)
        if pos_inicio == -1:
            continue
        pos_conteudo = pos_inicio + len(titulo)

        # O conteúdo vai até o próximo título ou o fim do texto
        pos_fim = len(texto)
        for proximo in titulos[i + 1 :]:
            pos = texto.find(proximo)
            if pos != -1:
                pos_fim = pos
                break

        conteudo = texto[pos_conteudo:pos_fim].strip()
        resultado[SECOES[titulo]] = conteudo

    # Se o parse falhou completamente, devolve o texto bruto em "resumo"
    if not resultado:
        resultado["resumo"] = texto

    return resultado
