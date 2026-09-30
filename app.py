import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="🪙",
    layout="centered"
)

# ============================================================
# ESTILO
# ============================================================

st.markdown("""
<style>
    .cashback-box {
        background: #f5f5f5;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
    }

    .cashback-value {
        font-size: 42px;
        font-weight: bold;
        margin: 10px 0 20px 0;
    }

    .progress-background {
        background: #dddddd;
        border-radius: 20px;
        height: 18px;
        overflow: hidden;
    }

    .progress-bar {
        height: 100%;
        background: #21a366;
        border-radius: 20px;
    }

    .bio-card {
        background: #f8f8f8;
        padding: 18px;
        border-radius: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DADOS DO PARTICIPANTE
# ============================================================

if "participante" not in st.session_state:
    st.session_state.participante = ""

if "carteira" not in st.session_state:
    st.session_state.carteira = ""

if "bio" not in st.session_state:
    st.session_state.bio = 0

if "cashback_resgatado" not in st.session_state:
    st.session_state.cashback_resgatado = 0.0

if "treinos" not in st.session_state:
    st.session_state.treinos = 0

if "comprovacoes" not in st.session_state:
    st.session_state.comprovacoes = 0

# ============================================================
# REGRAS
# ============================================================

LIMITE_BIO = 5000
VALOR_POR_BIO = 0.01
LIMITE_CASHBACK = 50.00

bio = st.session_state.bio

cashback_disponivel = min(
    bio * VALOR_POR_BIO,
    LIMITE_CASHBACK
)

porcentagem = min(
    bio / LIMITE_BIO,
    1
)

bio_faltante = max(
    LIMITE_BIO - bio,
    0
)

# ============================================================
# CABEÇALHO
# ============================================================

st.title("🪙 BioCore")

st.write(
    "Seu desafio. Seu BIO. Seu cashback."
)

st.divider()

# ============================================================
# CADASTRO
# ============================================================

st.subheader("👤 Participante")

nome = st.text_input(
    "Nome",
    value=st.session_state.participante,
    placeholder="Digite seu nome"
)

carteira = st.text_input(
    "Endereço da Trust Wallet",
    value=st.session_state.carteira,
    placeholder="Cole aqui o endereço público da sua carteira"
)

if st.button("💾 Salvar cadastro", use_container_width=True):

    if nome.strip() == "":
        st.warning("Digite seu nome.")

    elif carteira.strip() == "":
        st.warning("Digite o endereço público da sua Trust Wallet.")

    else:
        st.session_state.participante = nome
        st.session_state.carteira = carteira

        st.success("Cadastro salvo!")

# ============================================================
# PARTICIPANTE
# ============================================================

if st.session_state.participante:

    st.write(
        f"Olá, **{st.session_state.participante}**! 👋"
    )

# ============================================================
# MEU CASHBACK
# ============================================================

st.divider()

st.subheader("💰 Meu Cashback")

st.markdown(
    f"""
    <div class="cashback-box">

        <div>
            Cashback disponível
        </div>

        <div class="cashback-value">
            R$ {cashback_disponivel:,.2f}
        </div>

        <div class="progress-background">
            <div
                class="progress-bar"
                style="width: {porcentagem * 100}%;">
            </div>
        </div>

        <div style="margin-top: 12px;">
            <strong>{bio:,} / {LIMITE_BIO:,} BIO</strong>
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# MENSAGEM DA BARRA
# ============================================================

if bio < LIMITE_BIO:

    st.info(
        f"Faltam {bio_faltante:,} BIO "
        f"para chegar a R$ {LIMITE_CASHBACK:.2f}."
    )

else:

    st.success(
        "🎉 Você atingiu o limite de cashback deste ciclo!"
    )

# ============================================================
# SALDO
# ============================================================

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "🪙 Saldo BIO",
        f"{bio:,} BIO"
    )

with col2:

    st.metric(
        "💵 Cashback",
        f"R$ {cashback_disponivel:.2f}"
    )

# ============================================================
# TREINO
# ============================================================

st.divider()

st.subheader("🏋️ Treino")

st.write(
    "Registre sua atividade e acumule BIO."
)

if st.button(
    "🏋️ Registrar treino",
    use_container_width=True
):

    st.session_state.treinos += 1
    st.session_state.bio += 10

    st.success(
        "Treino registrado! +10 BIO"
    )

    st.rerun()

st.write(
    f"Treinos registrados: **{st.session_state.treinos}**"
)

# ============================================================
# COMPROVAÇÃO
# ============================================================

st.divider()

st.subheader("📸 Comprovação")

arquivo = st.file_uploader(
    "Envie a foto da sua atividade",
    type=["jpg", "jpeg", "png"]
)

if arquivo is not None:

    st.image(
        arquivo,
        caption="Comprovação enviada",
        use_container_width=True
    )

    if st.button(
        "📤 Enviar comprovação",
        use_container_width=True
    ):

        st.session_state.comprovacoes += 1
        st.session_state.bio += 70

        st.success(
            "Comprovação registrada! +70 BIO"
        )

        st.rerun()

# ============================================================
# TRUST WALLET
# ============================================================

st.divider()

st.subheader("👛 Minha Trust Wallet")

if st.session_state.carteira:

    st.code(
        st.session_state.carteira
    )

    st.caption(
        "Use somente o endereço público da carteira. "
        "Nunca informe sua frase de recuperação."
    )

else:

    st.warning(
        "Cadastre sua carteira para receber BIO."
    )

# ============================================================
# RESGATE
# ============================================================

st.divider()

st.subheader("🎁 Resgatar Cashback")

if cashback_disponivel > 0:

    st.write(
        f"Valor disponível: **R$ {cashback_disponivel:.2f}**"
    )

    if st.button(
        "💵 Solicitar cashback",
        use_container_width=True
    ):

        st.success(
            "Solicitação de cashback registrada!"
        )

        st.info(
            "O pagamento será analisado pelo BioCore."
        )

else:

    st.info(
        "Você ainda não possui cashback disponível."
    )

# ============================================================
# BIO
# ============================================================

st.divider()

st.subheader("🪙 Meu BIO")

st.write(
    f"Você possui **{st.session_state.bio:,} BIO**."
)

# ============================================================
# LOJAS
# ============================================================

st.divider()

st.subheader("🛒 Benefícios")

col1, col2 = st.columns(2)

with col1:

    st.link_button(
        "🛍️ Mercado Livre",
        "https://www.mercadolivre.com.br/",
        use_container_width=True
    )

with col2:

    st.link_button(
        "⚡ CoreStryke",
        "https://corestryke.com/",
        use_container_width=True
    )

# ============================================================
# RESUMO
# ============================================================

st.divider()

st.subheader("📊 Meu resumo")

st.write(
    f"👤 Participante: **{st.session_state.participante or 'Não cadastrado'}**"
)

st.write(
    f"🪙 BIO: **{st.session_state.bio:,}**"
)

st.write(
    f"💰 Cashback: **R$ {cashback_disponivel:.2f}**"
)

st.write(
    f"🏋️ Treinos: **{st.session_state.treinos}**"
)

st.write(
    f"📸 Comprovações: **{st.session_state.comprovacoes}**"
)
