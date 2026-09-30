import streamlit as st

st.set_page_config(
    page_title="BioCore",
    page_icon="🏋️"
)

# LOGIN
if "logado" not in st.session_state:
    st.session_state.logado = False

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


# ÁREA DO ALUNO

st.title("TREINO / ATIVIDADE FÍSICA")

st.write(
    f"Bem-vindo, **{st.session_state.usuario}**!"
)

st.divider()

st.subheader("🏋️ Treino")

st.button(
    "Registrar treino",
    use_container_width=True
)

st.subheader("🏃 Atividade Física")

st.button(
    "Registrar atividade física",
    use_container_width=True
)

st.subheader("📸 Comprovante")

st.file_uploader(
    "Enviar foto",
    type=["jpg", "jpeg", "png"]
)

st.divider()

if st.button("Sair", use_container_width=True):
    st.session_state.logado = False
    st.rerun()

