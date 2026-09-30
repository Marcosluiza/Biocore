import streamlit as st

st.set_page_config(
    page_title="BioCore",
    page_icon="🟢",
    layout="centered"
)

# =========================
# LINKS
# =========================

MERCADO_LIVRE = "https://www.mercadolivre.com.br/social/sama6231844"

BATTLE_WITHIN = "https://drive.google.com/file/d/1VoOv0AacWqtweJBlmXd6awJe-bOdmfRX/view?usp=drivesdk"

CORESTRYKE = "https://corestryke.com"

TRUST_WALLET = "https://trustwallet.com/"

# =========================
# ESTILO
# =========================

st.markdown("""
<style>

.block-container {
    max-width: 600px;
    padding-top: 30px;
}

h1 {
    text-align: center;
}

.subtitulo {
    text-align: center;
    font-size: 18px;
    margin-bottom: 25px;
}

.botao {
    display: block;
    width: 100%;
    padding: 16px;
    margin: 12px 0;
    border-radius: 12px;
    text-align: center;
    text-decoration: none;
    font-size: 18px;
    font-weight: bold;
    background: #eeeeee;
    color: #111111;
}

.botao:hover {
    opacity: 0.85;
}

.bio {
    padding: 18px;
    border-radius: 15px;
    background: #f1f1f1;
    text-align: center;
    margin: 20px 0;
}

</style>
""", unsafe_allow_html=True)

# =========================
# CABEÇALHO
# =========================

st.title("🟢 BioCore")

st.markdown(
    '<div class="subtitulo">Treino • Atividade Física • BIO • Benefícios</div>',
    unsafe_allow_html=True
)

# =========================
# TREINO
# =========================

st.markdown("## 🏋️ Treino / Atividade Física")

st.markdown("""
<div class="bio">
Registre suas atividades físicas e participe do sistema de recompensas BioCore.
</div>
""", unsafe_allow_html=True)

# =========================
# BATTLE WITHIN
# =========================

st.markdown("## 🎮 Battle Within")

st.markdown("""
<div class="bio">
Jogue o Battle Within no seu celular Android.
</div>
""", unsafe_allow_html=True)

st.markdown(
    f'<a class="botao" href="{BATTLE_WITHIN}" target="_blank">'
    '🎮 BAIXAR BATTLE WITHIN'
    '</a>',
    unsafe_allow_html=True
)

# =========================
# MERCADO LIVRE
# =========================

st.markdown("## 🛒 Mercado Livre")

st.markdown(
    f'<a class="botao" href="{MERCADO_LIVRE}" target="_blank">'
    '🛒 COMPRAR NO MERCADO LIVRE'
    '</a>',
    unsafe_allow_html=True
)

# =========================
# CORESTRYKE
# =========================

st.markdown("## 🏪 CoreStryke")

st.markdown(
    f'<a class="botao" href="{CORESTRY
