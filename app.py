import streamlit as st

st.set_page_config(
    page_title="BioCore",
    page_icon="🪙",
    layout="centered"
)

# =========================
# DADOS
# =========================

if "nome" not in st.session_state:
    st.session_state.nome = ""

if "carteira" not in st.session_state:
    st.session_state.carteira = ""

if "bio" not in st.session_state:
    st.session_state.bio = 0

if "treinos" not in st.session_state:
    st.session_state.treinos = 0

if "comprovacoes" not in st.session_state:
    st.session_state.comprovacoes = 0

# =========================
# REGRAS DO BIOCORE
# =========================

LIMITE_BIO = 5000
VALOR_BIO = 0.01
LIMITE_CASHBACK = 50.00

bio = st.session_state.bio

cashback = min(
    bio * VALOR_BIO,
    LIMITE_CASHBACK
)

porcentagem = min(
    bio / LIMITE_BIO,
    1.0
)

faltam = max(
    LIMITE_BIO - bio,
    0
)

# =========================
# ESTILO
# =========================

st.markdown("""
<style>

.main-title {
    text-align: center;
    font-size: 38px;
    font-weight: bold;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    margin-bottom: 25px;
}

.cashback-box {
    background-color: #f5f5f5;
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    margin-top: 10px;
    margin-bottom: 20px;
}

.cashback-title {
    font-size: 18px;
}

.cashback-value {
    font-size: 42px;
    font-weight: bold;
    margin: 10px 0 20px 0;
}

.progress-background {
    background-color: #dddddd;
    border-radius: 20px;
    height: 18px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    border-radius: 20px;
    background-color: #21a366;
}

.bio-text {
    margin-top: 12px;
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# CABEÇALHO
# =========================

st.markdown(
    '<div class="main-title">🪙 BioCore</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Seu desafio. Seu BIO. Seu cashback.</div>',
    unsafe_allow_html=True
)

st.divider()

# =========================
# PARTICIPANTE
# =========================

st.subheader("👤 Participante")

nome = st.text_input(
    "Nome",
    value=st.session_state.nome,
    placeholder="Digite seu nome"
)

carteira = st.text_input(
    "Endereço da Trust Wallet",
    value=st.session_state.carteira,
    placeholder="Cole aqui o endereço público da sua carteira"
)

if st.button(
    "💾 Salvar cadastro",
    use_container_width=True
):

    if nome.strip() == "":
        st.warning("Digite seu nome.")

    elif carteira.strip() == "":
        st.warning(
            "Digite o endereço público da sua Trust Wallet."
        )

    else:

        st.session_state.nome = nome
        st.session_state.carteira = carteira

        st.success("Cadastro salvo com sucesso!")

st.divider()

# =========================
# MEU CASHBACK
# =========================

st.subheader("💰 Meu Cashback")

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
            <strong>{bio:,} / {LIMITE_BIO:,} BIO</strong>
        </div>

    </div>
    """,
    unsafe_allow_html=True
)

if bio < LIMITE_BIO:

    st.info(
        f"Faltam {faltam:,} BIO para chegar a R$ 50,00."
    )

else:

    st.success(
        "🎉 Você atingiu R$ 50,00 de cashback!"
    )

# =========================
# SALDOS
# =========================

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "🪙 Saldo BIO",
        f"{bio:,} BIO"
    )

with col2:

    st.metric(
        "💵 Cashback",
        f"R$ {cashback:.2f}"
    )

# =========================
# TREINOS
# =========================

st.divider()

st.subheader("🏋️ Treinos")

st.write(
    "Registre seu treino e acumule BIO."
)

if st.button(
    "🏋️ Registrar treino +10 BIO",
    use_container_width=True
):

    st.session_state.treinos += 1
    st.session_state.bio += 10

    st.success(
        "Treino registrado! Você ganhou 10 BIO."
    )

    st.rerun()

st.write(
    f"Treinos registrados: {st.session_state.treinos}"
)

# =========================
# COMPROVAÇÃO
# =========================

st.divider()

st.subheader("📸 Comprovação")

arquivo = st.file_uploader(
    "Envie a foto do seu treino",
    type=["jpg", "jpeg", "png"]
)

if arquivo is not None:

    st.image(
        arquivo,
        caption="Comprovação do treino",
        use_container_width=True
    )

    if st.button(
        "📤 Enviar comprovação +70 BIO",
        use_container_width=True
    ):

        st.session_state.comprovacoes += 1
        st.session_state.bio += 70

        st.success(
            "Comprovação enviada! Você ganhou 70 BIO."
        )

        st.rerun()

# =========================
# TRUST WALLET
# =========================

st.divider()

st.subheader("👛 Minha Trust Wallet")

if st.session_state.carteira:

    st.code(
        st.session_state.carteira
    )

    st.caption(
        "Esse é o endereço público da sua carteira."
    )

else:

    st.info(
        "Cadastre sua Trust Wallet acima."
    )

# =========================
# RESGATAR CASHBACK
# =========================

st.divider()

st.subheader("🎁 Resgatar Cashback")

st.write(
    f"Cashback disponível: **R$ {cashback:.2f}**"
)

if cashback > 0:

    if st.button(
        "💵 Solicitar cashback",
        use_container_width=True
    ):

        st.success(
            "Solicitação de cashback enviada!"
        )

        st.info(
            "O BioCore irá analisar e processar o pagamento."
        )

else:

    st.warning(
        "Você ainda não possui cashback disponível."
    )

# =========================
# BIO
# =========================

st.divider()

st.subheader("🪙 Meu BIO")

st.write(
    f"Saldo atual: **{bio:,} BIO**"
)

# =========================
# BENEFÍCIOS
# =========================

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

# =========================
# RESUMO
# =========================

st.divider()

st.subheader("📊 Meu resumo")

st.write(
    f"👤 **Participante:** "
    f"{st.session_state.nome or 'Não cadastrado'}"
)

st.write(
    f"🪙 **BIO:** {st.session_state.bio:,}"
)

st.write(
    f"💰 **Cashback:** R$ {cashback:.2f}"
)

st.write(
    f"🏋️ **Treinos:** {st.session_state.treinos}"
)

st.write(
    f"📸 **Comprovações:** {st.session_state.comprovacoes}"
)
