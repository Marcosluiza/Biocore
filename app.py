import streamlit as st

# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="BioCore",
    page_icon="🪙",
    layout="centered"
)

LIMITE_BIO = 5000
VALOR_POR_BIO = 0.01

BIO_TREINO = 10
BIO_FOTO = 70

SENHA_ADMIN = "1234"


# =========================
# MEMÓRIA DA SESSÃO
# =========================

if "participantes" not in st.session_state:
    st.session_state.participantes = {}

if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = ""

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False


# =========================
# ESTILO
# =========================

st.markdown(
    """
    <style>

    .cashback-box {
        background: #f5f5f5;
        padding: 20px;
        border-radius: 15px;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .cashback-title {
        font-size: 16px;
        font-weight: bold;
    }

    .cashback-value {
        font-size: 32px;
        font-weight: bold;
        margin-top: 5px;
        margin-bottom: 15px;
    }

    .progress-background {
        width: 100%;
        height: 18px;
        background: #dddddd;
        border-radius: 10px;
        overflow: hidden;
    }

    .progress-bar {
        height: 18px;
        background: #20c997;
        border-radius: 10px;
    }

    .bio-text {
        margin-top: 10px;
        font-size: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# CABEÇALHO
# =========================

st.title("🪙 BioCore")
st.write("Seu desafio. Seu BIO. Seu cashback.")


# =========================
# ABAS
# =========================

aba_participante, aba_admin = st.tabs(
    ["👤 Participante", "🔐 Administrador"]
)


# ============================================================
# PARTICIPANTE
# ============================================================

with aba_participante:

    st.header("👤 Participante")

    nome = st.text_input(
        "Nome",
        placeholder="Digite seu nome"
    )

    carteira = st.text_input(
        "Endereço da Trust Wallet",
        placeholder="Cole aqui seu endereço público da carteira"
    )

    if st.button("💾 Salvar cadastro", use_container_width=True):

        if nome.strip() == "":
            st.warning("Digite seu nome.")

        elif carteira.strip() == "":
            st.warning("Digite o endereço da Trust Wallet.")

        else:

            nome = nome.strip()

            if nome not in st.session_state.participantes:

                st.session_state.participantes[nome] = {
                    "carteira": carteira,
                    "bio": 0,
                    "treinos": 0,
                    "fotos": 0,
                    "cashback_solicitado": 0
                }

            else:

                st.session_state.participantes[nome]["carteira"] = carteira

            st.session_state.usuario_atual = nome

            st.success("Cadastro salvo!")


    # =========================
    # ÁREA DO USUÁRIO
    # =========================

    usuario = st.session_state.usuario_atual

    if usuario in st.session_state.participantes:

        dados = st.session_state.participantes[usuario]

        st.divider()

        st.subheader("💰 Meu Cashback")

        bio = dados["bio"]

        if bio > LIMITE_BIO:
            bio_exibido = LIMITE_BIO
        else:
            bio_exibido = bio

        cashback = bio_exibido * VALOR_POR_BIO

        if cashback > 50:
            cashback = 50

        porcentagem = bio_exibido / LIMITE_BIO

        if porcentagem > 1:
            porcentagem = 1


        # =========================
        # CAIXA DE CASHBACK
        # =========================

        st.markdown(
            f"""
            <div class="cashback-box">

                <div class="cashback-title">
                    Cashback disponível
                </div>

                <div class="cashback-value">
                    R$ {cashback:.2f}
                </div>

                <div class="progress-background">

                    <div
                        class="progress-bar"
                        style="width: {porcentagem * 100}%;">
                    </div>

                </div>

                <div class="bio-text">
                    <strong>{bio_exibido:,} / {LIMITE_BIO:,} BIO</strong>
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        faltam = LIMITE_BIO - bio_exibido

        if faltam > 0:

            st.write(
                f"Faltam **{faltam:,} BIO** para chegar a R$50,00."
            )

        else:

            st.success("🎉 Você atingiu o limite de R$50,00.")


        # =========================
        # DADOS
        # =========================

        st.write("### 📊 Meu progresso")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "BIO",
                f"{dados['bio']:,}"
            )

        with col2:
            st.metric(
                "Treinos",
                dados["treinos"]
            )


        st.divider()


        # =========================
        # TREINO
        # =========================

        st.subheader("🏋️ Registrar treino")

        if st.button(
            f"➕ Registrar treino +{BIO_TREINO} BIO",
            use_container_width=True
        ):

            dados["bio"] += BIO_TREINO
            dados["treinos"] += 1

            st.success(
                f"Treino registrado! +{BIO_TREINO} BIO"
            )

            st.rerun()


        # =========================
        # FOTO
        # =========================

        st.subheader("📸 Comprovação semanal")

        foto = st.file_uploader(
            "Envie a foto do treino",
            type=["jpg", "jpeg", "png"]
        )

        if foto is not None:

            if st.button(
                f"📤 Enviar comprovação +{BIO_FOTO} BIO",
                use_container_width=True
            ):

                dados["bio"] += BIO_FOTO
                dados["fotos"] += 1

                st.success(
                    f"Comprovação enviada! +{BIO_FOTO} BIO"
                )

                st.rerun()


        st.divider()


        # =========================
        # TRUST WALLET
        # =========================

        st.subheader("👛 Minha Trust Wallet")

        st.code(
            dados["carteira"]
        )


        # =========================
        # SOLICITAR CASHBACK
        # =========================

        st.subheader("💵 Solicitar cashback")

        if bio >= LIMITE_BIO:

            if st.button(
                "💰 Solicitar R$50,00",
                use_container_width=True
            ):

                dados["cashback_solicitado"] = 50

                st.success(
                    "Solicitação enviada para o administrador."
                )

        else:

            st.info(
                "Você precisa chegar a 5.000 BIO para solicitar até R$50,00."
            )


        st.divider()


        # =========================
        # LOJAS
        # =========================

        st.subheader("🛍️ Parceiros")

        st.link_button(
            "🛒 Mercado Livre",
            "https://www.mercadolivre.com.br/social/sama6231844",
            use_container_width=True
        )

        st.link_button(
            "🏪 CoreStryke",
            "https://corestryke.com",
            use_container_width=True
        )


# ============================================================
# ADMINISTRADOR
# ============================================================

with aba_admin:

    st.header("🔐 Administrador")

    if not st.session_state.admin_logado:

        senha = st.text_input(
            "Senha do administrador",
            type="password"
        )

        if st.button(
            "🔓 Entrar",
           
