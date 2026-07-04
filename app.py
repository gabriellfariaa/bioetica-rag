"""
app.py
======
Interface Streamlit do BioéticaRAG.

Execute com:
    streamlit run app.py
"""

from pathlib import Path
import streamlit as st

# ---------------------------------------------------------------------------
# Configuração da página — deve ser o primeiro comando Streamlit
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BioéticaRAG",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Cabeçalho principal */
.cabecalho {
    border-left: 5px solid #1a5c96;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1.5rem;
    background: #f0f6ff;
    border-radius: 0 10px 10px 0;
}
.cabecalho h1 {
    font-family: 'Source Serif 4', serif;
    font-size: 1.8rem;
    font-weight: 600;
    color: #0d3d6e;
    margin: 0 0 0.2rem;
}
.cabecalho p { margin: 0; color: #3a5f84; font-size: 0.88rem; }

/* Cards de seção */
.card {
    background: #ffffff;
    border: 1px solid #dce6f0;
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1rem;
}
.card h3 {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1a5c96;
    margin: 0 0 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* Checklist */
.checklist-linha {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.45rem 0.6rem;
    border-bottom: 1px solid #eef2f7;
    font-size: 0.88rem;
    color: #2d3f50;
}
.checklist-linha:last-child { border-bottom: none; }
.badge-sim   { background:#dcfce7; color:#14532d; padding:2px 11px; border-radius:99px; font-size:0.75rem; font-weight:600; }
.badge-nao   { background:#f1f5f9; color:#334155; padding:2px 11px; border-radius:99px; font-size:0.75rem; font-weight:600; }
.badge-indet { background:#fef9c3; color:#713f12; padding:2px 11px; border-radius:99px; font-size:0.75rem; font-weight:600; }

/* Aviso legal */
.aviso {
    background: #fff7ed;
    border-left: 4px solid #f97316;
    padding: 0.7rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.81rem;
    color: #7c3d12;
    margin-top: 1.2rem;
    line-height: 1.5;
}

/* Tag de fonte */
.fonte-tag {
    font-family: 'IBM Plex Mono', monospace;
    background: #e0e7ff;
    color: #312e81;
    padding: 1px 7px;
    border-radius: 4px;
    font-size: 0.73rem;
}

/* Botão primário */
.stButton > button {
    background: #1a5c96 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 7px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.45rem 1.4rem !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #154e82 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Verificar se o banco vetorial existe
# ---------------------------------------------------------------------------
CHROMA_DIR = Path(__file__).parent / "chroma_db"
RAG_OK = CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())

# Importar o motor RAG somente se o banco existir
if RAG_OK:
    try:
        from rag_engine import analisar_projeto, consulta_livre, gerar_checklist
        RAG_IMPORTADO = True
    except Exception as e:
        RAG_IMPORTADO = False
        ERRO_IMPORT = str(e)
else:
    RAG_IMPORTADO = False

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚕️ BioéticaRAG")
    st.caption("Triagem ética preliminar de projetos de pesquisa")
    st.divider()

    pagina = st.radio(
        "Navegação",
        [
            "🏠  Início",
            "🔍  Analisar Projeto",
            "💬  Perguntar às Normas",
            "✅  Checklist Ético",
            "📋  Exemplos de Casos",
            "ℹ️  Sobre",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    if RAG_OK and RAG_IMPORTADO:
        st.success("Base documental carregada")
    elif RAG_OK and not RAG_IMPORTADO:
        st.error(f"Erro ao carregar o motor RAG:\n{ERRO_IMPORT}")
    else:
        st.warning(
            "Base documental não encontrada.\n\n"
            "Execute primeiro:\n```\npython setup_rag.py\n```"
        )

    st.caption("Este sistema **não** substitui avaliação formal pelo CEP/CONEP.")


# ---------------------------------------------------------------------------
# Helpers de renderização
# ---------------------------------------------------------------------------

def _badge(valor: str) -> str:
    if valor == "Sim":
        return '<span class="badge-sim">Sim</span>'
    elif valor == "Não":
        return '<span class="badge-nao">Não</span>'
    return '<span class="badge-indet">Indeterminado</span>'


def _renderizar_analise(resultado: dict):
    """Exibe o resultado da análise em expanders organizados."""
    secoes = [
        ("📋 Resumo do projeto",                        "resumo",           True),
        ("📜 Normas aplicáveis",                        "normas",           False),
        ("🏛 CEP e/ou CONEP",                           "cep_conep",        True),
        ("⚖️ Requisitos éticos",                        "requisitos_eticos", False),
        ("🔒 LGPD e dados sensíveis",                   "lgpd",             False),
        ("📝 TCLE",                                     "tcle",             True),
        ("⚠️ Riscos regulatórios",                      "riscos",           False),
        ("ℹ️ Limitações desta análise",                  "limitacoes",       False),
    ]
    for titulo, chave, aberto in secoes:
        conteudo = resultado.get(chave, "")
        if conteudo:
            with st.expander(titulo, expanded=aberto):
                st.markdown(conteudo)


def _renderizar_checklist(checklist: dict):
    """Exibe o checklist como tabela HTML estilizada."""
    itens = [
        ("Envolve seres humanos?",          checklist.get("seres_humanos", "Indeterminado")),
        ("Envolve dados pessoais sensíveis?", checklist.get("dados_sensiveis", "Indeterminado")),
        ("Envolve material biológico?",     checklist.get("material_biologico", "Indeterminado")),
        ("Envolve dados genéticos?",        checklist.get("dados_geneticos", "Indeterminado")),
        ("Envolve populações vulneráveis?", checklist.get("populacoes_vulneraveis", "Indeterminado")),
        ("Exige TCLE?",                     checklist.get("tcle", "Indeterminado")),
        ("Exige submissão ao CEP?",         checklist.get("cep", "Indeterminado")),
        ("Exige análise pela CONEP?",       checklist.get("conep", "Indeterminado")),
    ]
    html = '<div class="card" style="padding:0.4rem 0.6rem">'
    for criterio, valor in itens:
        html += f'<div class="checklist-linha"><span>{criterio}</span>{_badge(valor)}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    obs = checklist.get("observacoes", "")
    if obs:
        st.info(f"**Observações:** {obs}")


# ---------------------------------------------------------------------------
# Fallback de demonstração (sem RAG configurado)
# ---------------------------------------------------------------------------

def _demo_analise(descricao: str) -> dict:
    d = descricao.lower()
    cep  = "provável" if any(w in d for w in ["paciente","participante","voluntário","entrevista","criança"]) else "verificar"
    lgpd = "dados sensíveis identificados" if any(w in d for w in ["diagnóstico","saúde","médico","genético"]) else "verificar necessidade"
    return {
        "resumo": f"**(Modo demonstração — RAG não configurado)**\n\n{descricao[:300]}...",
        "normas": "- Resolução CNS nº 466/2012\n- Resolução CNS nº 510/2016\n- Lei nº 13.709/2018 (LGPD)",
        "cep_conep": f"**{cep.capitalize()}**. Configure o RAG para análise fundamentada nas normas.",
        "requisitos_eticos": "- Consentimento dos participantes\n- Proteção de dados\n- Minimização de riscos",
        "lgpd": lgpd,
        "tcle": "Provável necessidade — confirme após configurar a base documental.",
        "riscos": "Execute `python setup_rag.py` para análise real dos riscos regulatórios.",
        "limitacoes": "Esta é uma demonstração. A análise real requer a base documental indexada.",
    }


def _demo_consulta(pergunta: str) -> tuple:
    return (
        f"**(Modo demonstração)** Para responder à pergunta *\"{pergunta}\"* com base nas "
        "normas reais, execute `python setup_rag.py` para indexar os documentos.",
        [],
    )


def _demo_checklist(descricao: str) -> dict:
    d = descricao.lower()
    return {
        "seres_humanos":        "Sim"  if any(w in d for w in ["paciente","participante","voluntário","pessoa","adolescente"]) else "Indeterminado",
        "dados_sensiveis":      "Sim"  if any(w in d for w in ["diagnóstico","saúde","médico","clínico","psiquiátrico"]) else "Indeterminado",
        "material_biologico":   "Sim"  if any(w in d for w in ["sangue","tecido","amostra","biológico","biobanco"]) else "Não",
        "dados_geneticos":      "Sim"  if any(w in d for w in ["genétic","genôm","dna","sequenciamento"]) else "Não",
        "populacoes_vulneraveis":"Sim" if any(w in d for w in ["adolescente","criança","quilombola","indígena","preso","idoso"]) else "Não",
        "tcle":                 "Sim"  if any(w in d for w in ["entrevista","coleta","participante","voluntário"]) else "Indeterminado",
        "cep":                  "Sim"  if any(w in d for w in ["humano","paciente","participante","voluntário","prontuário"]) else "Indeterminado",
        "conep":                "Sim"  if any(w in d for w in ["genétic","quilombola","indígena","biobanco","embrião"]) else "Indeterminado",
        "observacoes":          "Resultado baseado em palavras-chave (modo demonstração). Configure o RAG para análise real.",
    }


# ---------------------------------------------------------------------------
# CASOS DE EXEMPLO
# ---------------------------------------------------------------------------
CASOS = {
    "Entrevistas sobre saúde mental em adolescentes": {
        "desc": (
            "Estudo qualitativo com entrevistas semiestruturadas sobre saúde mental em "
            "adolescentes de 14 a 17 anos matriculados em escolas públicas. Serão coletados "
            "nome, idade, diagnósticos psiquiátricos prévios e histórico familiar de transtornos. "
            "As entrevistas serão gravadas em áudio. Pesquisador vinculado à USP."
        ),
        "tag": "Vulneráveis · Dados sensíveis · CEP obrigatório",
    },
    "Análise retrospectiva de prontuários oncológicos": {
        "desc": (
            "Estudo retrospectivo com acesso a 500 prontuários de pacientes oncológicos "
            "de 2018 a 2023 em hospital universitário. Dados coletados: nome, CPF, diagnóstico, "
            "protocolo de tratamento e resultados de exames genéticos. Sem contato direto com pacientes."
        ),
        "tag": "LGPD · Dados genéticos · Possível CONEP",
    },
    "Survey anônimo sobre hábitos alimentares": {
        "desc": (
            "Questionário online totalmente anônimo aplicado a adultos acima de 18 anos sobre "
            "hábitos alimentares. Nenhum dado identificador será coletado. Participação voluntária "
            "via formulário público. Sem riscos físicos ou psicológicos identificados."
        ),
        "tag": "Risco mínimo · Possível dispensa de CEP",
    },
    "Genômica de comunidades quilombolas com biobanco": {
        "desc": (
            "Pesquisa de genômica populacional com coleta de sangue de 200 voluntários de "
            "comunidades quilombolas. Sequenciamento genômico completo. Material armazenado "
            "em biobanco por 10 anos. Parceria com laboratório internacional."
        ),
        "tag": "CONEP obrigatório · Biobanco · Populações vulneráveis",
    },
    "IA para predição de risco cardiovascular": {
        "desc": (
            "Desenvolvimento de modelo de machine learning para predição de risco cardiovascular "
            "usando dataset de 50.000 pacientes com exames laboratoriais, imagens e dados clínicos "
            "anonimizados de hospital universitário. Sem coleta prospectiva."
        ),
        "tag": "LGPD · Anonimização · CEP provável",
    },
}


# ============================================================================
# PÁGINAS
# ============================================================================

# --- INÍCIO ------------------------------------------------------------------
if pagina == "🏠  Início":
    st.markdown("""
    <div class="cabecalho">
        <h1>⚕️ BioéticaRAG</h1>
        <p>Assistente inteligente para triagem ética preliminar de projetos de pesquisa no contexto brasileiro.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card">
            <h3>O que este sistema faz</h3>
            <ul style="color:black;font-size:0.88rem; margin:0; padding-left:1.1rem; line-height:1.9">
                <li>Analisa projetos sob a ótica ética brasileira</li>
                <li>Identifica necessidade de CEP e/ou CONEP</li>
                <li>Verifica implicações da LGPD e dados sensíveis</li>
                <li>Sinaliza necessidade de TCLE / TALE</li>
                <li>Gera checklist ético automático</li>
                <li>Responde dúvidas sobre normas e resoluções</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <h3>Base normativa</h3>
            <ul style="color:black;font-size:0.88rem; margin:0; padding-left:1.1rem; line-height:1.9">
                <li>Resolução CNS nº 466/2012</li>
                <li>Resolução CNS nº 510/2016</li>
                <li>Resolução CNS nº 441/2011</li>
                <li>Resolução CNS nº 340/2004</li>
                <li>Resolução CNS nº 580/2018</li>
                <li>Lei nº 13.709/2018 — LGPD</li>
                <li>Documentos CEP/CONEP · Plataforma Brasil</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    if not RAG_OK:
        st.warning(
            "**Base documental não indexada.** O sistema funcionará em modo de demonstração "
            "(respostas baseadas em palavras-chave, sem consulta real às normas).\n\n"
            "Para habilitar o RAG completo:\n"
            "1. Adicione os PDFs das normas na pasta `docs/`\n"
            "2. Execute `python setup_rag.py`"
        )
    else:
        st.info("👈 Use o menu lateral para começar. Recomendamos **Analisar Projeto** ou **Exemplos de Casos**.")


# --- ANALISAR PROJETO --------------------------------------------------------
elif pagina == "🔍  Analisar Projeto":
    st.header("Análise Ética de Projeto de Pesquisa")
    st.caption("Descreva o projeto com o máximo de detalhes. Quanto mais contexto, mais precisa a análise.")

    descricao = st.text_area(
        "Descrição do projeto",
        placeholder=(
            "Ex: Pesquisa qualitativa com entrevistas sobre saúde mental em adolescentes de 14–17 anos. "
            "Dados coletados: nome, idade, diagnósticos. Participantes recrutados em escola pública..."
        ),
        height=210,
        key="desc_projeto",
    )

    col_btn, _ = st.columns([1, 5])
    with col_btn:
        analisar = st.button("Analisar", type="primary", use_container_width=True)

    if analisar:
        if not descricao.strip():
            st.warning("Descreva o projeto antes de analisar.")
        else:
            with st.spinner("Consultando a base normativa e gerando análise com Claude..."):
                if RAG_IMPORTADO:
                    resultado = analisar_projeto(descricao)
                else:
                    resultado = _demo_analise(descricao)

            st.divider()
            _renderizar_analise(resultado)
            st.markdown("""
            <div class="aviso">
                ⚠️ <strong>Aviso:</strong> Esta análise é orientativa e preliminar.
                Não substitui avaliação formal pelo CEP/CONEP nem constitui parecer jurídico.
                Submeta o projeto ao sistema oficial antes de iniciar a pesquisa.
            </div>
            """, unsafe_allow_html=True)


# --- PERGUNTAR ÀS NORMAS -----------------------------------------------------
elif pagina == "💬  Perguntar às Normas":
    st.header("Consulta Livre à Base Normativa")
    st.caption("Faça perguntas diretas sobre as resoluções, LGPD, CEP/CONEP e outros temas.")

    SUGESTOES = [
        "Qual é a função do TCLE?",
        "Qual a diferença entre CEP e CONEP?",
        "Qual a diferença entre biobanco e biorrepositório?",
        "Como a LGPD se aplica a dados de saúde?",
        "Quando uma pesquisa dispensa TCLE?",
        "Quais riscos éticos há em pesquisas com genética humana?",
        "Quando a pesquisa precisa ir direto à CONEP?",
        "O que é dado sensível segundo a LGPD?",
    ]

    st.markdown("**Sugestões:**")
    cols = st.columns(4)
    for i, s in enumerate(SUGESTOES):
        with cols[i % 4]:
            if st.button(s, key=f"sug_{i}", use_container_width=True):
                st.session_state["pergunta_input"] = s

    st.divider()

    pergunta = st.text_input(
        "Sua pergunta",
        value=st.session_state.get("pergunta_input", ""),
        placeholder="Digite sua dúvida sobre ética em pesquisa...",
    )

    if st.button("Perguntar", type="primary") and pergunta.strip():
        with st.spinner("Buscando nas normas..."):
            if RAG_IMPORTADO:
                resposta, fontes = consulta_livre(pergunta)
            else:
                resposta, fontes = _demo_consulta(pergunta)

        st.markdown("### Resposta")
        st.markdown(resposta)

        if fontes:
            with st.expander("Trechos recuperados da base documental"):
                for i, f in enumerate(fontes, 1):
                    st.markdown(f"**Trecho {i}** — `{f['source']}`")
                    st.caption(f["content"])
                    if i < len(fontes):
                        st.divider()

        st.markdown("""
        <div class="aviso">
            ⚠️ Consulte sempre os textos oficiais para decisões formais.
            Esta resposta é gerada com base nos documentos indexados e pode conter imprecisões.
        </div>
        """, unsafe_allow_html=True)


# --- CHECKLIST ÉTICO ---------------------------------------------------------
elif pagina == "✅  Checklist Ético":
    st.header("Checklist Ético Automático")
    st.caption("Descreva o projeto para gerar um checklist com os critérios éticos identificados.")

    desc_check = st.text_area(
        "Descrição do projeto",
        placeholder="Descreva brevemente o projeto...",
        height=170,
    )

    if st.button("Gerar Checklist", type="primary") and desc_check.strip():
        with st.spinner("Analisando critérios éticos..."):
            if RAG_IMPORTADO:
                checklist = gerar_checklist(desc_check)
            else:
                checklist = _demo_checklist(desc_check)

        st.divider()
        _renderizar_checklist(checklist)
        st.markdown("""
        <div class="aviso">
            ⚠️ Itens "Indeterminado" requerem análise mais detalhada por especialista ou pelo CEP.
        </div>
        """, unsafe_allow_html=True)


# --- EXEMPLOS DE CASOS -------------------------------------------------------
elif pagina == "📋  Exemplos de Casos":
    st.header("Exemplos de Casos de Pesquisa")
    st.caption("Casos pré-configurados para demonstração do sistema.")

    caso_nome = st.selectbox("Selecione um caso:", list(CASOS.keys()))
    caso = CASOS[caso_nome]

    st.markdown(f"""
    <div class="card">
        <h3>{caso_nome}</h3>
        <p style="font-size:0.88rem; color:#2d3f50; line-height:1.75; margin:0 0 0.6rem">
            {caso['desc']}
        </p>
        <span class="fonte-tag">{caso['tag']}</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Analisar este caso", use_container_width=True):
            with st.spinner("Analisando..."):
                if RAG_IMPORTADO:
                    resultado = analisar_projeto(caso["desc"])
                else:
                    resultado = _demo_analise(caso["desc"])
            st.divider()
            _renderizar_analise(resultado)

    with col2:
        if st.button("✅ Checklist deste caso", use_container_width=True):
            with st.spinner("Gerando checklist..."):
                if RAG_IMPORTADO:
                    checklist = gerar_checklist(caso["desc"])
                else:
                    checklist = _demo_checklist(caso["desc"])
            st.divider()
            _renderizar_checklist(checklist)


# --- SOBRE -------------------------------------------------------------------
elif pagina == "ℹ️  Sobre":
    st.header("Sobre o BioéticaRAG")

    st.markdown("""
    <div class="card">
        <h3>Objetivo</h3>
        <p style="color:black;font-size:0.88rem; line-height:1.75; margin:0">
        Apoiar pesquisadores na identificação inicial de requisitos éticos, documentais e regulatórios
        de projetos de pesquisa no contexto brasileiro, com base nas resoluções do CNS e na LGPD.
        </p>
    </div>

    <div class="card">
        <h3>Arquitetura técnica</h3>
        <p style="color:black;font-size:0.88rem; line-height:1.75; margin:0">
        <strong>RAG (Retrieval-Augmented Generation)</strong> com:<br>
        • <strong>LangChain</strong> — orquestração do pipeline<br>
        • <strong>Chroma DB</strong> — banco vetorial dos documentos normativos<br>
        • <strong>OpenAI text-embedding-3-small</strong> — geração dos embeddings<br>
        • <strong>Claude (Anthropic)</strong> — modelo de linguagem para as respostas<br>
        • <strong>Streamlit</strong> — interface web
        </p>
    </div>

    <div class="card">
        <h3>Limitações importantes</h3>
        <ul style="color:black;font-size:0.88rem; line-height:1.9; margin:0; padding-left:1.1rem">
            <li>Não substitui avaliação formal pelo CEP/CONEP</li>
            <li>Não constitui parecer jurídico definitivo</li>
            <li>A qualidade depende dos documentos indexados e da recuperação RAG</li>
            <li>Casos complexos requerem análise presencial com especialista</li>
            <li>A análise deve ser tratada como orientação inicial e preliminar</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
