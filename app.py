import streamlit as st
import sqlite3
import hashlib

st.set_page_config(
    page_title="BioCore",
    page_icon="🟢"
)

DB = "biocore.db"


def conectar():
    return sqlite3.connect(DB)


def criar_banco():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            bio INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def criar_conta(nome, email, senha):
    conn = conectar()
    c = conn.cursor()

    try:
        c.execute(
            """
            INSERT INTO participantes
            (nome, email, senha, bio)
            VALUES (?, ?, ?, 0)
            """,
            (
                nome,
                email.lower(),
                hash_senha(senha)
            )
        )

        conn.commit()
        return True, "Conta criada com sucesso!"

    except sqlite3.IntegrityError:
        return False, "Esse e-mail já está cadastrado."

    finally:
        conn.close()


def fazer_login(email, senha):
    conn = conectar()
    c = conn.cursor()

    c.execute(
        """
        SELECT id, nome, bio
        FROM participantes
        WHERE email = ? AND senha = ?
        """,
        (
            email.lower(),
            hash_senha(senha)
        )
    )

    resultado = c.fetchone()

    conn.close()

    return resultado


criar_banco()


if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None


if not st.session_state.logado:

    st.title("🟢 BioCore")

    st.subheader("Treino • Atividade Física • Recompensas")

    login, cadastro = st.tabs([
        "Entrar",
        "Criar conta"
    ])

    with login:

        st.markdown("### 🔐 Entrar")

        email = st.text_input(
            "E-mail"
        )

        senha = st.text_input(
            "Senha",
            type="password"
        )

        if st.button(
            "Entrar",
            use_container_width=True
        ):

            usuario = fazer_login(
                email,
                senha
            )

            if usuario:

                st.session_state.logado = True
                st.session_state.usuario_id = usuario[0]

                st.rerun()

            else:

                st.error(
                    "E-mail ou senha incorretos."
                )


    with cadastro:

        st.markdown("### 👤 Criar conta")

        nome = st.text_input(
            "Nome"
        )

        email_cadastro = st.text_input(
            "E-mail"
        )

        senha_cadastro = st.text_input(
            "Senha",
            type="password"
        )

        confirmar = st.text_input(
            "Confirmar senha",
            type="password"
        )

        if st.button(
            "Criar minha conta",
            use_container_width=True
        ):

            if not nome or not email_cadastro or not senha_cadastro:

                st.error(
                    "Preencha todos os campos."
                )

            elif senha_cadastro != confirmar:

                st.error(
                    "As senhas não são iguais."
                )

            elif len(senha_cadastro) < 6:

                st.error(
                    "A senha precisa ter pelo menos 6 caracteres."
                )

            else:

                sucesso, mensagem = criar_conta(
                    nome,
                    email_cadastro,
                    senha_cadastro
                )

                if sucesso:

                    st.success(mensagem)

                else:

                    st.error(mensagem)

    st.stop()


usuario_id = st.session_state.usuario_id

conn = conectar()
c = conn.cursor()

c.execute(
    """
    SELECT nome, email, bio
    FROM participantes
    WHERE id = ?
    """,
    (usuario_id,)
)

usuario = c.fetchone()

conn.close()


st.title("🟢 BioCore")

st.write(
    f"Olá, **{usuario[0]}**!"
)

st.metric(
    "Seu saldo BIO",
    usuario[2]
)

st.metric(
    "Valor",
    f"R$ {usuario[2] / 100:.2f}"
)

if st.button(
    "Sair",
    use_container_width=True
):

    st.session_state.logado = False
    st.session_state.usuario_id = None

    st.rerun()
