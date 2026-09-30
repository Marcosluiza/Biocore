import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="🪙",
    layout="centered"
)

LIMITE_BIO = 5000
VALOR_BIO = 0.01

BIO_TREINO = 10
BIO_FOTO = 70

SENHA_ADMIN = "1234"


# ============================================================
# MEMÓRIA
# ============================================================

if "usuarios" not in st.session_state:
    st.session_state.usuarios = {}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>

    .cashback-box {
        background: #f3f3f3;
        padding: 20px;
        border-radius: 15px;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .cashback-titulo {
        font-size: 16px;
        font-weight: bold;
    }

    .cashback-valor {
        font-size: 32px;
        font-weight: bold;
        margin-top: 5px;
        margin-bottom: 15px;
    }

    .barra-fundo {
        width: 100%;
        height: 18px;
        background: #dddddd;
        border-radius: 10px;
        overflow: hidden;
    }

    .barra {
        height: 18px;
        background: #20c997;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CABEÇALHO
# ============================================================

st.title("🪙 BioCore")
st.write("Seu desafio. Seu BIO. Seu cashback.")


# ============================================================
# SE O PARTICIPANTE ESTIVER LOGADO
# ============================================================

if st.session_state.usuario_logado is not None:

    email_logado = st.session_state.usuario_logado
    dados = st.session_state.usuarios[email_logado]

    st.success(
        f"Olá, {dados['
