import streamlit as st

st.set_page_config(
    page_title="BioCore",
    page_icon="🏋️",
    layout="centered"
)

# =========================
# LOGIN
# =========================

if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if not st.session_state.logado:

    st.title("BioCore")
    st.subheader("Acesso do aluno")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", use_container_width=True):

        if usuario == "aluno1" and senha == "BioCore@2026!Teste":
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.rerun()

        else:
            st.error("Usuário ou senha incorretos.")

    st.stop()


# =========================
# ÁREA DO ALUNO
# =========================

st.title("TREINO / ATIVIDADE FÍSICA")

st.write(
    f"Bem-vindo, **{st.session_state.usuario}**!"
)

st.divider()

# TREINO
st.subheader("🏋️ Treino")

if st.button("Registrar treino", use_container_width=True):
    st.success("Treino registrado!")


# ATIVIDADE FÍSICA
st.subheader("🏃 Atividade Física")

if st.button("Registrar atividade física", use_container_width=True):
    st.success("Atividade física registrada!")


# COMPROVANTE
st.subheader("📸 Comprovante")

foto = st.file_uploader(
    "Enviar foto do treino ou atividade",
    type=["jpg", "jpeg", "png"]
)

if foto is not None:
    st.success("Foto recebida!")


# BIO
st.divider()

st.subheader("🪙 BIO")

st.write("Saldo atual: **0 BIO**")

st.write("Histórico de recompensas aparecerá aqui.")


# SAIR
st.divider()

if st.button("Sair", use_container_width=True):
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.rerun()
