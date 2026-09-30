import streamlit as st
import sqlite3
from datetime import date, datetime, timedelta
import hashlib

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="🟢",
    layout="centered"
)

# =========================================================
# LINKS
# =========================================================

MERCADO_LIVRE = "https://www.mercadolivre.com.br/social/sama6231844"

CORESTRYKE = "https://corestryke.com"

TRUST_WALLET = "https://trustwallet.com/"

# Link do Battle Within
BATTLE_WITHIN_ID = "1VoOv0AacWqtweJBlmXd6awJe-bOdmfRX"

BATTLE_WITHIN = (
    f"https://drive.google.com/uc?export=download&id={BATTLE_WITHIN_ID}"
)

# =========================================================
# REGRAS DE RECOMPENSA
# =========================================================

BIO_TREINO = 10
BIO_FOTO_SEMANAL = 70

MINIMO_SAQUE = 5000
MINIMO_COMPRAS = 2

# =========================================================
# RECOMPENSA DAS 40 FASES
# =========================================================
#
# Fases 1-10  = 10 BIO
# Fases 11-20 = 20 BIO
# Fases 21-30 = 30 BIO
# Fases 31-40 = 40 BIO
#
# Total = 1.000 BIO
#

def recompensa_fase(fase):
    if 1 <= fase <= 10:
        return 10
    elif 11 <= fase <= 20:
        return 20
    elif 21 <= fase <= 30:
        return 30
    elif 31 <= fase <= 40:
        return 40
    return 0


# =========================================================
# BANCO DE DADOS
# =========================================================

DB = "biocore.db"


def conectar():
    return sqlite3.connect(DB, check_same_thread=False)


def criar_banco():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            bio REAL DEFAULT 0,
            compras_qualificadas INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            data TEXT,
            tipo TEXT,
            bio INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            semana TEXT,
            nome_arquivo TEXT,
            bio INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            fase INTEGER,
            bio INTEGER,
            UNIQUE(participante_id, fase)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            data TEXT,
            valor_compra REAL,
            comissao REAL,
            percentual REAL,
            bio REAL,
            validada INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            data TEXT,
            bio INTEGER,
            valor_reais REAL,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


criar_banco()


# =========================================================
# FUNÇÕES DO BANCO
# =========================================================

def criar_participante(nome):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM participantes WHERE nome = ?",
        (nome,)
    )

    resultado = cursor.fetchone()

    if resultado:
        participante_id = resultado[0]

    else:
        cursor.execute(
            "INSERT INTO participantes (nome) VALUES (?)",
            (nome,)
        )

        participante_id = cursor.lastrowid
        conn.commit()

    conn.close()

    return participante_id


def buscar_participante(participante_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, nome, bio, compras_qualificadas
        FROM participantes
        WHERE id = ?
        """,
        (participante_id,)
    )

    resultado = cursor.fetchone()

    conn.close()

    return resultado


def adicionar_bio(participante_id, quantidade):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
        """,
        (quantidade, participante_id)
    )

    conn.commit()
    conn.close()


def treino_hoje(participante_id):

    hoje = str(date.today())

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM treinos
        WHERE participante_id = ?
        AND data = ?
        """,
        (participante_id, hoje)
    )

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None


def registrar_treino(participante_id, tipo):

    hoje = str(date.today())

    if treino_hoje(participante_id):
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO treinos
        (participante_id, data, tipo, bio)
        VALUES (?, ?, ?, ?)
        """,
        (
            participante_id,
            hoje,
            tipo,
            BIO_TREINO
        )
    )

    conn.commit()
    conn.close()

    adicionar_bio(participante_id, BIO_TREINO)

    return True


def semana_atual():

    hoje = date.today()

    inicio = hoje - timedelta(days=hoje.weekday())

    return str(inicio)


def foto_semana_existe(participante_id):

    semana = semana_atual()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM fotos
        WHERE participante_id = ?
        AND semana = ?
        """,
        (participante_id, semana)
    )

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None


def registrar_foto(participante_id, nome_arquivo):

    semana = semana_atual()

    if foto_semana_existe(participante_id):
        return False

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO fotos
        (participante_id, semana, nome_arquivo, bio)
        VALUES (?, ?, ?, ?)
        """,
        (
            participante_id,
            semana,
            nome_arquivo,
            BIO_FOTO_SEMANAL
        )
    )

    conn.commit()
    conn.close()

    adicionar_bio(participante_id, BIO_FOTO_SEMANAL)

    return True


def fase_concluida(participante_id, fase):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM fases
        WHERE participante_id = ?
        AND fase = ?
        """,
        (participante_id, fase)
    )

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None


def registrar_fase(participante_id, fase):

    if fase_concluida(participante_id, fase):
        return False

    bio = recompensa_fase(fase)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO fases
        (participante_id, fase, bio)
        VALUES (?, ?, ?)
        """,
        (
            participante_id,
            fase,
            bio
        )
    )

    conn.commit()
    conn.close()

    adicionar_bio(participante_id, bio)

    return True


def registrar_compra(
    participante_id,
    valor_compra,
    comissao
):

    # 25% da comissão recebida
    bio = comissao * 0.25

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO compras
        (
            participante_id,
            data,
            valor_compra,
            comissao,
            percentual,
            bio,
            validada
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            participante_id,
            str(date.today()),
            valor_compra,
            comissao,
            25,
            bio,
            0
        )
    )

    conn.commit()
    conn.close()

    return bio


def validar_compra(compra_id, participante_id, bio):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT validada
        FROM compras
        WHERE id = ?
        AND participante_id = ?
        """,
        (compra_id, participante_id)
    )

    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False

    if resultado[0] == 1:
        conn.close()
        return False

    cursor.execute(
        """
        UPDATE compras
        SET validada = 1
        WHERE id = ?
        AND participante_id = ?
        """,
        (compra_id, participante_id)
    )

    cursor.execute(
        """
        UPDATE participantes
        SET bio = bio + ?,
            compras_qualificadas =
                compras_qualificadas + 1
        WHERE id = ?
        """,
        (bio, participante_id)
    )

    conn.commit()
    conn.close()

    return True


# =========================================================
# ESTILO
# =========================================================

st.markdown("""
<style>

.block-container {
    max-width: 650px;
    padding-top: 25px;
    padding-bottom: 50px;
}

.bio-header {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
}

.subtitulo {
    text-align: center;
    font-size: 18px;
    margin-bottom: 25px;
}

.card {
    padding: 20px;
    border-radius: 16px;
    background: #f1f1f1;
    margin: 15px 0;
}

.saldo {
    text-align: center;
    padding: 25px;
    border-radius: 18px;
    background: #eeeeee;
    margin: 20px 0;
}

.saldo-numero {
    font-size: 38px;
    font-weight: bold;
}

.botao {
    display: block;
    width: 100%;
    padding: 16px;
    margin: 10px 0;
    border-radius: 12px;
    text-align: center;
    text-decoration: none;
    font-size: 18px;
    font-weight: bold;
    background: #eeeeee;
    color: #111111;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# CABEÇALHO
# =========================================================

st.markdown(
    '<div class="bio-header">🟢 BioCore</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo">'
    'Treino • Atividade Física • BIO • Benefícios'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# IDENTIFICAÇÃO
# =========================================================

st.subheader("👤 Participante")

nome = st.text_input(
    "Digite seu nome",
    placeholder="Seu nome"
)

if not nome:

    st.info(
        "Digite seu nome para acessar sua área do BioCore."
    )

    st.stop()


nome = nome.strip()

if len(nome) < 2:

    st.warning(
        "Digite um nome válido."
    )

    st.stop()


participante_id = criar_participante(nome)

participante = buscar_participante(participante_id)

saldo = participante[2]
compras_qualificadas = participante[3]


# =========================================================
# SALDO
# =========================================================

st.markdown(
    f"""
    <div class="saldo">
        <div>💰 MEU CASHBACK</div>
        <div class="saldo-numero">{saldo:.0f} BIO</div>
        <div>Equivalente máximo: R$ {saldo / 100:.2f}</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    "Referência atual: 5.000 BIO = R$50."
)


# =========================================================
# TREINO
# =========================================================

st.header("🏋️ Treino / Atividade Física")

treinos = [
    "Peito / Ombro / Tríceps",
    "Dorsal / Bíceps",
    "Quadríceps / Glúteo / Panturrilha",
    "Perna completa",
    "Abdômen",
    "Peso corporal",
    "Corrida",
    "Futebol"
]

if treino_hoje(participante_id):

    st.success(
        "✅ Você já registrou seu treino de hoje e recebeu 10 BIO."
    )

else:

    treino = st.selectbox(
        "O que você treinou hoje?",
        treinos
    )

    if st.button(
        "🏋️ REGISTRAR TREINO +10 BIO",
        use_container_width=True
    ):

        sucesso = registrar_treino(
            participante_id,
            treino
        )

        if sucesso:

            st.success(
                f"Treino registrado: {treino}. "
                f"+{BIO_TREINO} BIO!"
            )

            st.rerun()

        else:

            st.warning(
                "Você já registrou um treino hoje."
            )


# =========================================================
# FOTO SEMANAL
# =========================================================

st.header("📸 Foto semanal")

if foto_semana_existe(participante_id):

    st.success(
        "✅ A foto desta semana já foi registrada. "
        "Você recebeu 70 BIO."
    )

else:

    st.write(
        "Envie uma foto semanal para comprovar sua participação."
    )

    foto = st.file_uploader(
        "Escolha sua foto",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )

    if foto:

        st.image(
            foto,
            caption="Foto selecionada",
            use_container_width=True
        )

        if st.button(
            "📸 ENVIAR FOTO +70 BIO",
            use_container_width=True
        ):

            sucesso = registrar_foto(
                participante_id,
                foto.name
            )

            if sucesso:

                st.success(
                    "Foto registrada! +70 BIO."
                )

                st.rerun()

            else:

                st.warning(
                    "A foto desta semana já foi registrada."
                )


# =========================================================
# BATTLE WITHIN
# =========================================================

st.header("🎮 Battle Within")

st.write(
    "Avance nas 40 fases e registre cada fase concluída "
    "para receber BIO."
)

st.markdown(
    f"""
    <a class="botao"
       href="{BATTLE_WITHIN}"
       target="_blank">
       🎮 BAIXAR BATTLE WITHIN
    </a>
    """,
    unsafe_allow_html=True
)

fase = st.number_input(
    "Qual fase você concluiu?",
    min_value=1,
    max_value=40,
    step=1
)

bio_fase = recompensa_fase(fase)

st.write(
    f"Recompensa da fase {fase}: **{bio_fase} BIO**"
)

if fase_concluida(participante_id, fase):

    st.success(
        f"✅ A fase {fase} já foi registrada."
    )

else:

    if st.button(
        f"🎮 REGISTRAR FASE {fase} +{bio_fase} BIO",
        use_container_width=True
    ):

        sucesso = registrar_fase(
            participante_id,
            fase
        )

        if sucesso:

            st.success(
                f"Fase {fase} registrada! "
                f"+{bio_fase} BIO."
            )

            st.rerun()


# =========================================================
# TABELA DAS FASES
# =========================================================

with st.expander("📋 Ver recompensas das 40 fases"):

    for i in range(1, 41):

        recompensa = recompensa_fase(i)

        if fase_concluida(participante_id, i):

            st.write(
                f"✅ Fase {i}: {recompensa} BIO"
            )

        else:

            st.write(
                f"⬜ Fase {i}: {recompensa} BIO"
            )


# =========================================================
# MERCADO LIVRE
# =========================================================

st.header("🛒 Mercado Livre")

st.write(
    "Faça suas compras através do nosso link de afiliado."
)

st.markdown(
    f"""
    <a class="botao"
       href="{MERCADO_LIVRE}"
       target="_blank">
       🛒 COMPRAR PELO MERCADO LIVRE
    </a>
    """,
    unsafe_allow_html=True
)

st.info(
    "25% da comissão de afiliado recebida "
    "é destinada à recompensa em BIO."
)


# =========================================================
# REGISTRO DE COMPRA
# =========================================================

with st.expander("🧾 Registrar compra qualificada"):

    st.write(
        "A compra precisa ser validada antes de gerar BIO."
    )

    valor_compra = st.number_input(
        "Valor da compra (R$)",
        min_value=0.0,
        step=1.0
    )

    comissao = st.number_input(
        "Comissão de afiliado recebida (R$)",
        min_value=0.0,
        step=0.01
    )

    bio_compra = comissao * 0.25

    st.write(
        f"BIO a receber após validação: "
        f"**{bio_compra:.2f} BIO**"
    )

    if st.button(
        "🧾 ENVIAR COMPRA PARA VALIDAÇÃO",
        use_container_width=True
    ):

        if valor_compra <= 0:

            st.warning(
                "Informe o valor da compra."
            )

        elif comissao <= 0:

            st.warning(
                "Informe a comissão recebida."
            )

        else:

            registrar_compra(
                participante_id,
                valor_compra,
                comissao
            )

            st.success(
                "Compra enviada para validação."
            )


# =========================================================
# STATUS PARA SAQUE
# =========================================================

st.header("💸 Cashback")

st.write(
    f"BIO acumulado: **{saldo:.0f} BIO**"
)

st.write(
    f"Compras qualificadas: "
    f"**{compras_qualificadas} de {MINIMO_COMPRAS}**"
)

if saldo >= MINIMO_SAQUE and compras_qualificadas >= MINIMO_COMPRAS:

    st.success(
        "✅ Você atingiu os requisitos para solicitar o cashback!"
    )

    if st.button(
        "💸 SOLICITAR CASHBACK",
        use_container_width=True
    ):

        valor = saldo / 100

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO saques
            (participante_id, data, bio, valor_reais, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                participante_id,
                str(date.today()),
                saldo,
                valor,
                "Solicitado"
            )
        )

        conn.commit()
        conn.close()

        st.success(
            f"Solicitação enviada: "
            f"{saldo:.0f} BIO = R$ {valor:.2f}"
        )

else:

    falta_bio = max(
        0,
        MINIMO_SAQUE - saldo
    )

    falta_compras = max(
        0,
        MINIMO_COMPRAS - compras_qualificadas
    )

    st.warning(
        f"Para solicitar o cashback, faltam "
        f"**{falta_bio:.0f} BIO** e "
        f"**{falta_compras} compra(s) qualificada(s)**."
    )


# =========================================================
# CORESTRYKE
# =========================================================

st.header("🏪 CoreStryke")

st.markdown(
    f"""
    <a class="botao"
       href="{CORESTRYKE}"
       target="_blank">
       🏪 ACESSAR CORESTRYKE
    </a>
    """,
    unsafe_allow_html=True
)


# =========================================================
# TRUST WALLET
# =========================================================

st.header("👛 Trust Wallet")

st.markdown(
    f"""
    <a class="botao"
       href="{TRUST_WALLET}"
       target="_blank">
       👛 ACESSAR TRUST WALLET
    </a>
    """,
    unsafe_allow_html=True
)


# =========================================================
# REGRAS
# =========================================================

st.header("📜 Regras do BioCore")

with st.expander("📜 VER TODAS AS REGRAS"):

    st.markdown("""
### 🏋️ Treinos

- Cada participante pode registrar **1 treino por dia**.
- Cada treino válido gera **10 BIO**.
- Um segundo treino no mesmo dia não gera BIO adicional.

### 📸 Foto semanal

- Cada participante pode enviar **1 foto por semana**.
- A foto semanal gera **70 BIO**.
- A mesma semana não pode gerar uma segunda recompensa.

### 🎮 Battle Within

- O Battle Within possui **40 fases**.
- Cada fase pode gerar BIO somente uma vez por participante.
- Fases 1–10: **10 BIO por fase**.
- Fases 11–20: **20 BIO por fase**.
- Fases 21–30: **30 BIO por fase**.
- Fases 31–40: **40 BIO por fase**.
- Completar todas as 40 fases representa **1.000 BIO**.

### 🛒 Mercado Livre

- O participante deve utilizar o **link de afiliado do BioCore**.
- A recompensa corresponde a **25% da comissão de afiliado efetivamente recebida**.
- A compra precisa ser validada antes do lançamento da recompensa.

### 💰 Cashback

- Referência atual: **5.000 BIO = R$50**.
- Para solicitar o cashback, o participante precisa:
  - ter pelo menos **5.000 BIO**;
  - ter pelo menos **2 compras qualificadas** pelo link de afiliado.
- O saldo de BIO não significa pagamento automático.
- As atividades e compras estão sujeitas à validação.

### 🔒 Integridade

- Uma mesma atividade não pode ser utilizada repetidamente para gerar a mesma recompensa.
- Fases já registradas não geram BIO novamente.
- O BioCore pode verificar as atividades e compras antes de validar recompensas.
""")


# =========================================================
# RODAPÉ
# =========================================================

st.markdown("---")

st.caption(
    "BioCore • Treino • Atividade Física • BIO • Battle Within"
)
