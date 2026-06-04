import streamlit as st
# Force refresh 12

import os
from datetime import datetime
import utils.document_processor as doc_proc
from utils.docx_exporter import create_legal_docx
import utils.ai_client_v3
import importlib
importlib.reload(utils.ai_client_v3)
from utils.ai_client_v3 import configure_ai, generate_legal_document
from dotenv import load_dotenv, set_key

# Configura a página
st.set_page_config(page_title="Dr. Estranho IA", page_icon="⚖️", layout="wide")

# Tenta carregar variáveis de ambiente
load_dotenv()
if "GEMINI_API_KEY" in os.environ:
    configure_ai()

# Custom CSS Premium e Moderno
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #e0e8f0 100%);
    }
    
    /* Box do conteúdo principal */
    .css-1d391kg, .st-emotion-cache-1wmy9hl {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    /* Botões Padrão */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
        color: white !important;
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(79, 70, 229, 0.4);
    }
    
    /* Botão de Download */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    .stDownloadButton>button:hover {
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
    }
    
    /* Inputs e TextAreas */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #4f46e5;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Headers
st.title("⚖️ Dr. Estranho IA")
st.markdown("**Sistema Inteligente para Redação Automática de Peças Jurídicas de Alta Complexidade.**")

# Estado da sessão
if "documents_text" not in st.session_state:
    st.session_state.documents_text = ""
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None
if "docx_file" not in st.session_state:
    st.session_state.docx_file = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "user"
if "username" not in st.session_state:
    st.session_state.username = ""

import utils.auth_manager as auth_manager

# Sistema de Login Seguro com Firebase
if not st.session_state.authenticated:
    st.markdown("---")
    colA, colB, colC = st.columns([1, 2, 1])
    with colB:
        with st.container(border=True):
            st.subheader("🔒 Acesso Restrito")
            user_input = st.text_input("Usuário")
            pass_input = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                user_data = auth_manager.verify_login(user_input, pass_input)
                if user_data:
                    st.session_state.authenticated = True
                    st.session_state.username = user_data["username"]
                    st.session_state.user_role = user_data["role"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos! (Ou erro no Firebase)")
            
            st.info("💡 Para ativar novos usuários, coloque o arquivo `firebase_key.json` na pasta do app.")
    st.stop() # Bloqueia o restante do app se não logar!

# Sidebar para API e Configurações
with st.sidebar:
    st.markdown(f"👤 Logado como: **{st.session_state.username}**")
    if st.session_state.user_role == "admin":
        with st.expander("👑 Painel do Administrador", expanded=False):
            st.markdown("### Gerenciar Usuários")
            try:
                # Criar Usuário
                with st.form("form_novo_user"):
                    novo_user = st.text_input("Novo Usuário")
                    nova_senha = st.text_input("Nova Senha", type="password")
                    cargo = st.selectbox("Cargo", ["user", "admin"])
                    if st.form_submit_button("Cadastrar"):
                        auth_manager.create_user(novo_user, nova_senha, cargo)
                        st.success(f"Usuário {novo_user} criado!")
                
                # Listar / Deletar Usuários
                st.markdown("---")
                users = auth_manager.list_users()
                for u in users:
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"`{u['username']}` ({u['role']})")
                    if c2.button("❌", key=f"del_{u['username']}"):
                        auth_manager.delete_user(u['username'])
                        st.rerun()
            except Exception as e:
                st.error("⚠️ Banco de Dados (Firebase) não configurado.")
                st.caption(str(e))
    st.divider()
    
    st.header("⚙️ Configurações do Sistema")
    
    # Campo de chave API com placeholder mostrando se já tem salvo
    has_saved_key = bool(os.getenv("GEMINI_API_KEY"))
    placeholder_text = "Chave já salva na memória!" if has_saved_key else "Cole sua Chave API aqui"
    
    api_key_input = st.text_input("Chave API Gemini", type="password", placeholder=placeholder_text)
    
    # Salva a chave automaticamente se o usuário digitar uma nova
    if api_key_input and api_key_input != os.getenv("GEMINI_API_KEY"):
        set_key(".env", "GEMINI_API_KEY", api_key_input)
        load_dotenv(override=True)
        configure_ai(api_key_input)
        st.success("✅ Chave API salva permanentemente!")
    elif has_saved_key:
        st.success("✅ Sistema Autenticado")
    
    st.divider()
    st.markdown("### 📂 Documentos Carregados")
    uploaded_files = st.file_uploader("Arraste arquivos PDF, DOCX ou TXT", accept_multiple_files=True, type=['pdf', 'docx', 'txt'])
    
    if st.button("🔄 Processar Documentos"):
        if uploaded_files:
            with st.spinner("Extraindo texto dos arquivos..."):
                combined_text = ""
                for file in uploaded_files:
                    try:
                        text = doc_proc.extract_text(file, file.name)
                        combined_text += f"\n\n--- DOCUMENTO: {file.name} ---\n{text}"
                    except Exception as e:
                        st.error(f"Erro no arquivo {file.name}: {e}")
                
                st.session_state.documents_text = combined_text
                st.success("Documentos lidos com sucesso!")
        else:
            st.warning("Envie pelo menos um arquivo.")
            
    st.divider()
    if st.button("🚪 Sair (Logout)", type="secondary"):
        st.session_state.authenticated = False
        st.rerun()
@st.dialog("📄 Pré-visualização da Peça em Página Inteira", width="large")
def fullscreen_preview_modal(text):
    st.markdown(text)

# Área Principal
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. Configurar o Pedido")
    
    # Orientações permanentes
    system_instructions = st.text_area(
        "Orientações Permanentes (Estilo, Limitações)",
        value="Você é um advogado brasileiro de altíssimo nível, especialista em contencioso cível. Redija a peça jurídica solicitada baseando-se EXCLUSIVAMENTE nas informações dos documentos fornecidos e no pedido do usuário. Formate o texto final em Markdown bem estruturado, com títulos usando # e ##.",
        height=100
    )
    
    # Tipo de Peça e Extensão
    c1, c2 = st.columns(2)
    with c1:
        doc_type = st.selectbox("Qual peça deseja gerar?", [
            "Petição Inicial", "Contestação", "Réplica / Manifestação", 
            "Embargos de Declaração", "Contrarrazões aos Embargos", 
            "Recurso de Apelação", "Contrarrazões de Apelação", 
            "Agravo de Instrumento", "Petição Simples", "Outra Peça (Personalizada)"
        ])
    with c2:
        doc_length = st.selectbox("Extensão da Peça", ["Longa e Fundamentada", "Curta e Objetiva"])
    
    # Prompt detalhado
    user_prompt = st.text_area(
        "O que a IA deve focar nesta peça? (Detalhes e Teses)",
        placeholder="Descreva aqui os pontos principais, o que o juiz errou, as teses de defesa, etc...",
        height=150
    )
    
    # Assinatura (PADRÃO ATUALIZADO)
    signature_name = st.text_input("Nome do Advogado para Assinatura", "DIEGO DOS SANTOS HERNANDEZ")
    signature_oab = st.text_input("OAB para Assinatura", "OAB/RS N°71476")

    if st.button("🚀 Gerar Peça com IA", use_container_width=True):
        if not st.session_state.documents_text:
            st.error("Por favor, carregue e processe os documentos na barra lateral primeiro.")
        elif not os.getenv("GEMINI_API_KEY") and not api_key_input:
            st.error("Configura a Chave da API do Gemini na barra lateral.")
        else:
            with st.spinner("Analisando documentos e redigindo peça... Isso pode levar cerca de 1 a 2 minutos."):
                
                # Monta as instruções finais
                ext_instruction = "DIRETRIZ: Peça LONGA e EXAUSTIVA." if doc_length == "Longa e Fundamentada" else "DIRETRIZ: Peça CURTA e OBJETIVA."
                data_atual = datetime.now().strftime("%d de %B de %Y")
                sig_instruction = f"Termine a peça com um espaço para local e data ({data_atual}) e a assinatura de {signature_name}, {signature_oab}."
                
                final_system = f"{system_instructions}\n\n{ext_instruction}\n\n{sig_instruction}"
                
                # Contexto pro prompt
                tipo_peca_contexto = f"Você deve redigir a seguinte peça: {doc_type}.\n\n"
                
                try:
                    response_text = generate_legal_document(
                        system_instruction=final_system,
                        user_prompt=tipo_peca_contexto + user_prompt,
                        context_docs=st.session_state.documents_text
                    )
                    st.session_state.ai_response = response_text
                    
                    # Gera DOCX
                    docx_buffer = create_legal_docx(response_text)
                    st.session_state.docx_file = docx_buffer
                    st.success("Peça gerada com sucesso!")
                except Exception as e:
                    st.error(f"Ocorreu um erro: {e}")

with col2:
    st.subheader("2. Resultado e Exportação")
    
    if st.session_state.ai_response:
        st.markdown("### Pré-visualização")
        with st.container(height=500, border=True):
            st.markdown(st.session_state.ai_response)
        
        if st.button("🔍 Expandir em Página Inteira", use_container_width=True):
            fullscreen_preview_modal(st.session_state.ai_response)
            
        st.download_button(
            label="💾 Baixar Peça em Word (.docx)",
            data=st.session_state.docx_file,
            file_name="peca_juridica.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        
        st.divider()
        st.markdown("### Ajustes Finos (Refinar Peça)")
        refine_text = st.text_input("O que deseja alterar na peça gerada?")
        if st.button("Atualizar Peça"):
            st.info("Funcionalidade de refinamento contínuo em desenvolvimento para esta versão.")
            # Aqui entrará a função de refinamento usando histórico
    else:
        st.info("A peça gerada aparecerá aqui.")

