import streamlit as st

st.set_page_config(
    page_title="BioCore",
    page_icon="🪙",
    layout="centered"
)

# -------------------------
# CONFIGURAÇÕES
# -------------------------

LIMITE_BIO = 5000
BIO_TREINO = 10
BIO_FOTO = 70
SENHA_ADMIN = "1234"

# -------------------------
# MEMÓRIA
# -------------------------

if "participantes" not in st.session_state:
    st.session_state.participantes = {}

if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if "admin" not in st.session_state:
    st.session_state.admin = False

# -------------------------
# VISUAL
# -------------------------

st.markdown(
    """
    <style>
    .caixa {
        padding: 20px;
        border-radius: 15px;
        background-color: #f2f2f2;
        margin-bottom: 20px;
    }

    .valor {
        font-size: 32px;
        font-weight: bold;
    }

    .barra-fundo {
        width: 100%;
        height: 18px;
        background-color: #dddddd;
        border-radius: 10px;
        overflow: hidden;
    }

    .barra {
        height: 18px;
        background-color: #20c997;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------
# TÍTULO
# -------------------------

st.title("🪙 BioCore")
st.write("Seu desafio. Seu BIO. Seu cashback.")

# -------------------------
# ABAS
# -------------------------

participante, administrador = st.tabs(
    ["👤 Participante", "🔐 Administrador"]
)

# =====================================================
# PARTICIPANTE
# =====================================================

with participante:

    st.header("👤 Participante")

    nome = st.text_input("Nome")

    carteira = st.text_input(
        "Endereço da Trust Wallet"
    )

    if st.button(
        "💾 Salvar cadastro",
        use_container_width=True
    ):

        if nome == "":
            st.warning("Digite seu nome.")

        elif carteira == "":
            st.warning("Digite sua carteira.")

        else:

            if nome not in st.session_state.participantes:

                st.session_state.participantes[nome] = {
                    "carteira": carteira,
                    "bio": 0,
                    "treinos": 0,
                    "fotos": 0
                }

            else:

                st.session_state.participantes[nome]["carteira"] = carteira

            st.session_state.usuario = nome

            st.success("Cadastro salvo!")

    # -------------------------
    # DADOS DO PARTICIPANTE
    # -------------------------

    usuario = st.session_state.usuario

    if usuario != "" and usuario in st.session_state.participantes:

        dados = st.session_state.participantes[usuario]

        st.divider()

        st.subheader("💰 Meu Cashback")

        bio = dados["bio"]

        bio_barra = min(bio, LIMITE_BIO)

        cashback = bio_barra * 0.01

        cashback = min(cashback, 50)

        porcentagem = bio_barra / LIMITE_BIO

        st.markdown(
            f"""
            <div class="caixa">

                <div>Cashback disponível</div>

                <div class="valor">
                    R$ {cashback:.2f}
                </div>

                <div class="barra-fundo">

                    <div
                        class="barra"
                        style="width:{porcentagem * 100}%;">
                    </div>

                </div>

                <p>
                    <strong>
                    {bio_barra:,} / {LIMITE_BIO:,} BIO
                    </strong>
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        if bio_barra < LIMITE_BIO:

            faltam = LIMITE_BIO - bio_barra

            st.write(
                f"Faltam **{faltam:,} BIO** para chegar a R$50,00."
            )

        else:

            st.success(
                "🎉 Você chegou a R$50,00 de cashback."
            )

        # -------------------------
        # PROGRESSO
        # -------------------------

        st.subheader("📊 Meu progresso")

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

        # -------------------------
        # TREINO
        # -------------------------

        st.divider()

        st.subheader("🏋️ Treino")

        if st.button(
            "➕ Registrar treino +10 BIO",
            use_container_width=True
        ):

            dados["bio"] += BIO_TREINO
            dados["treinos"] += 1

            st.success(
                "Treino registrado! +10 BIO"
            )

            st.rerun()

        # -------------------------
        # FOTO
        # -------------------------

        st.subheader("📸 Comprovação")

        foto = st.file_uploader(
            "Enviar foto do treino",
            type=["jpg", "jpeg", "png"]
        )

        if foto is not None:

            if st.button(
                "📤 Enviar comprovação +70 BIO",
                use_container_width=True
            ):

                dados["bio"] += BIO_FOTO
                dados["fotos"] += 1

                st.success(
                    "Comprovação registrada! +70 BIO"
                )

                st.rerun()

        # -------------------------
        # CARTEIRA
        # -------------------------

        st.divider()

        st.subheader("👛 Minha Trust Wallet")

        st.code(
            dados["carteira"]
        )

        # -------------------------
        # CASHBACK
        # -------------------------

        st.subheader("💵 Cashback")

        if bio >= LIMITE_BIO:

            if st.button(
                "💰 Solicitar R$50,00",
                use_container_width=True
            ):

                st.success(
                    "Solicitação enviada ao administrador."
                )

        else:

            st.info(
                "Chegue a 5.000 BIO para solicitar até R$50,00."
            )

        # -------------------------
        # LINKS
        # -------------------------

        st.divider()

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


# =====================================================
# ADMINISTRADOR
# =====================================================

with administrador:

    st.header("🔐 Administrador")

    if not st.session_state.admin:

        senha = st.text_input(
            "Senha",
            type="password"
        )

        if st.button(
            "🔓 Entrar",
            use_container_width=True
        ):

            if senha == SENHA_ADMIN:

                st.session_state.admin = True

                st.rerun()

            else:

                st.error(
                    "Senha incorreta."
                )

    else:

        st.success(
            "Administrador conectado ✅"
        )

        if st.button(
            "🚪 Sair",
            use_container_width=True
        ):

            st.session_state.admin = False

            st.rerun()

        st.divider()

        st.subheader("📊 Resumo")

        participantes = st.session_state.participantes

        total = len(participantes)

        total_bio = sum(
            p["bio"]
            for p in participantes.values()
        )

        total_treinos = sum(
            p["treinos"]
            for p in participantes.values()
        )

        total_fotos = sum(
            p["fotos"]
            for p in participantes.values()
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Participantes",
                total
            )

        with col2:

            st.metric(
                "BIO",
                f"{total_bio:,}"
            )

        col3, col4 = st.columns(2)

        with col3:

            st.metric(
                "Treinos",
                total_treinos
            )

        with col4:

            st.metric(
                "Fotos",
                total_fotos
            )

        st.divider()

        st.subheader("👥 Participantes")

        if total == 0:

            st.info(
                "Nenhum participante cadastrado ainda."
            )

        else:

            for nome_pessoa, dados in participantes.items():

                with st.expander(
                    f"👤 {nome_pessoa}"
                ):

                    st.write(
                        f"🪙 BIO: {dados['bio']:,}"
                    )

                    st.write(
                        f"🏋️ Treinos: {dados['treinos']}"
                    )

                    st.write(
                        f"📸 Fotos: {dados['fotos']}"
                    )

                    st.write(
                        "👛 Trust Wallet:"
                    )

                    st.code(
                        dados["carteira"]
                    )

                    cashback = min(
                        dados["bio"] * 0.01,
                        50
                    )

                    st.write(
                        f"💰 Cashback: R$ {cashback:.2f}"
                    )

        st.divider()

        st.subheader("📜 Regras")

        st.write("🏋️ Treino = +10 BIO")
        st.write("📸 Foto semanal = +70 BIO")
        st.write("💰 5.000 BIO = até R$50,00")
        st.write("🪙 1 BIO = R$0,01")
