import streamlit as st
import sqlite3
import hashlib
from datetime import date, timedelta

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="🟢",
    layout="centered"
)

DB = "biocore.db"

MERCADO_LIVRE = "https://www.mercadolivre.com.br/social/sama6231844"
CORESTRYKE = "https://corestryke.com"
TRUST_WALLET = "https://trustwallet.com/"

BATTLE_WITHIN_ID = "1VoOv0AacWqtweJBlmXd6awJe-bOdmfRX"
BATTLE_WITHIN = (
    f"https://drive.google.com/uc?export=download&id={BATTLE_WITHIN_ID}"
)

BIO_TREINO = 10
BIO_FOTO = 70

MINIMO_SAQUE = 5000
MINIMO_COMPRAS = 2

# =========================================================
# BANCO
# =========================================================

def conectar():
    return sqlite3.connect(DB, check_same_thread=False)


def criar_banco():

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            bio REAL DEFAULT 0,
            compras_qualificadas INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            data TEXT,
            tipo TEXT,
            bio INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            semana TEXT,
            nome_arquivo TEXT,
            bio INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            fase INTEGER,
            bio INTEGER,
            UNIQUE(participante_id, fase)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            data TEXT,
            valor_compra REAL,
            comissao REAL,
            bio REAL,
            validada INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS saques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER,
            data TEXT,
            bio REAL,
            valor_reais REAL,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


criar_banco()

# =========================================================
# SENHA
# =========================================================

def hash_senha(senha):
    return hashlib.sha256(
        senha.encode("utf-8")
    ).hexdigest()


# =========================================================
# PARTICIPANTE
# =========================================================

def criar_conta(nome, email, senha):

    conn = conectar()
    c = conn.cursor()

    try:

        c.execute("""
            INSERT INTO participantes
            (nome, email, senha)
            VALUES (?, ?, ?)
        """, (
            nome,
            email.lower().strip(),
            hash_senha(senha)
        ))

        conn.commit()

        participante_id = c.lastrowid

        conn.close()

        return participante_id, None

    except sqlite3.IntegrityError:

        conn.close()

        return None, "Este e-mail já possui uma conta."


def login(email, senha):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT id, nome
        FROM participantes
        WHERE email = ?
        AND senha = ?
    """, (
        email.lower().strip(),
        hash_senha(senha)
    ))

    resultado = c.fetchone()

    conn.close()

    return resultado


def participante(id_participante):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT id, nome, email, bio, compras_qualificadas
        FROM participantes
        WHERE id = ?
    """, (id_participante,))

    resultado = c.fetchone()

    conn.close()

    return resultado


def adicionar_bio(id_participante, quantidade):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (
        quantidade,
        id_participante
    ))

    conn.commit()
    conn.close()

# =========================================================
# TREINO
# =========================================================

def treino_hoje(id_participante):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT id
        FROM treinos
        WHERE participante_id = ?
        AND data = ?
    """, (
        id_participante,
        str(date.today())
    ))

    resultado = c.fetchone()

    conn.close()

    return resultado is not None


def registrar_treino(id_participante, tipo):

    if treino_hoje(id_participante):
        return False

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO treinos
        (participante_id, data, tipo, bio)
        VALUES (?, ?, ?, ?)
    """, (
        id_participante,
        str(date.today()),
        tipo,
        BIO_TREINO
    ))

    conn.commit()
    conn.close()

    adicionar_bio(id_participante, BIO_TREINO)

    return True

# =========================================================
# FOTO SEMANAL
# =========================================================

def semana_atual():

    hoje = date.today()

    inicio = hoje - timedelta(
        days=hoje.weekday()
    )

    return str(inicio)


def foto_semana_existe(id_participante):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT id
        FROM fotos
        WHERE participante_id = ?
        AND semana = ?
    """, (
        id_participante,
        semana_atual()
    ))

    resultado = c.fetchone()

    conn.close()

    return resultado is not None


def registrar_foto(id_participante, nome):

    if foto_semana_existe(id_participante):
        return False

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO fotos
        (participante_id, semana, nome_arquivo, bio)
        VALUES (?, ?, ?, ?)
    """, (
        id_participante,
        semana_atual(),
        nome,
        BIO_FOTO
    ))

    conn.commit()
    conn.close()

    adicionar_bio(
        id_participante,
        BIO_FOTO
    )

    return True

# =========================================================
# BATTLE WITHIN
# =========================================================

def recompensa_fase(fase):

    if fase <= 10:
        return 10

    if fase <= 20:
        return 20

    if fase <= 30:
        return 30

    return 40


def fase_concluida(id_participante, fase):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT id
        FROM fases
        WHERE participante_id = ?
        AND fase = ?
    """, (
        id_participante,
        fase
    ))

    resultado = c.fetchone()

    conn.close()

    return resultado is not None


def registrar_fase(id_participante, fase):

    if fase_concluida(
        id_participante,
        fase
    ):
        return False

    bio = recompensa_fase(fase)

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO fases
        (participante_id, fase, bio)
        VALUES (?, ?, ?)
    """, (
        id_participante,
        fase,
        bio
    ))

    conn.commit()
    conn.close()

    adicionar_bio(
        id_participante,
        bio
    )

    return True

# =========================================================
# COMPRAS
# =========================================================

def registrar_compra(
    id_participante,
    valor,
    comissao
):

    bio = comissao * 0.25

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO compras
        (
            participante_id,
            data,
            valor_compra,
            comissao,
            bio,
            validada
        )
        VALUES (?, ?, ?, ?, ?, 0)
    """, (
        id_participante,
        str(date.today()),
        valor,
        comissao,
        bio
    ))

    conn.commit()
    conn.close()


def validar_compra(compra_id):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT participante_id, bio, validada
        FROM compras
        WHERE id = ?
    """, (compra_id,))

    compra = c.fetchone()

    if not compra:
        conn.close()
        return False

    participante_id = compra[0]
    bio = compra[1]
    validada = compra[2]

    if validada:
        conn.close()
        return False

    c.execute("""
        UPDATE compras
        SET validada = 1
        WHERE id = ?
    """, (compra_id,))

    c.execute("""
        UPDATE participantes
        SET bio = bio + ?,
            compras_qualificadas =
            compras_qualificadas + 1
        WHERE id = ?
    """, (
        bio,
        participante_id
    ))

    conn.commit()
    conn.close()

    return True

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.block-container {
    max-width: 650px;
    padding-top: 25px;
}

.titulo {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
}

.subtitulo {
    text-align: center;
    font-size: 18px;
    margin-bottom: 25px;
}

.saldo {
    text-align: center;
    padding: 25px;
    border-radius: 18px;
    background: #eeeeee;
    margin: 20px 0;
}

.numero {
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
# SESSÃO
# =========================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if "participante_id" not in st.session_state:
    st.session_state.participante_id = None

# =========================================================
# LOGIN / CADASTRO
# =========================================================

if not st.session_state.logado:

    st.markdown(
        '<div class="titulo">🟢 BioCore</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitulo">'
        'Treino • Atividade Física • BIO'
        '</div>',
        unsafe_allow_html=True
    )

    aba1, aba2 = st.tabs([
        "🔐 Entrar",
        "👤 Criar conta"
    ])

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    with aba1:

        email = st.text_input(
            "E-mail",
            key="login_email"
        )

        senha = st.text_input(
            "Senha",
            type="password",
            key="login_senha"
        )

        if st.button(
            "🔐 ENTRAR",
            use_container_width=True
        ):

            resultado = login(
                email,
                senha
            )

            if resultado:

                st.session_state.logado = True
                st.session_state.participante_id = resultado[0]

                st.rerun()

            else:

                st.error(
                    "E-mail ou senha incorretos."
                )

    # -----------------------------------------------------
    # CADASTRO
    # -----------------------------------------------------

    with aba2:

        nome = st.text_input(
            "Nome"
        )

        email = st.text_input(
            "E-mail",
            key="cadastro_email"
        )

        senha = st.text_input(
            "Senha",
            type="password",
            key="cadastro_senha"
        )

        confirmar = st.text_input(
            "Confirmar senha",
            type="password"
        )

        if st.button(
            "👤 CRIAR MINHA CONTA",
            use_container_width=True
        ):

            if not nome or not email or not senha:

                st.warning(
                    "Preencha todos os campos."
                )

            elif senha != confirmar:

                st.error(
                    "As senhas não são iguais."
                )

            elif len(senha) < 6:

                st.error(
                    "A senha precisa ter pelo menos 6 caracteres."
                )

            else:

                id_novo, erro = criar_conta(
                    nome,
                    email,
                    senha
                )

                if erro:

                    st.error(erro)

                else:

                    st.success(
                        "Conta criada! Agora faça o login."
                    )

    st.stop()

# =========================================================
# ÁREA LOGADA
# =========================================================

id_participante = st.session_state.participante_id

dados = participante(id_participante)

if not dados:

    st.session_state.logado = False
    st.rerun()

nome = dados[1]
saldo = dados[3]
compras = dados[4]

st.markdown(
    '<div class="titulo">🟢 BioCore</div>',
    unsafe_allow_html=True
)

st.write(
    f"Olá, **{nome}**!"
)

if st.button(
    "🚪 Sair",
    use_container_width=True
):

    st.session_state.logado = False
    st.session_state.participante_id = None

    st.rerun()

# =========================================================
# SALDO
# =========================================================

st.markdown(
    f"""
    <div class="saldo">
        <div>💰 MEU CASHBACK</div>
        <div class="numero">{saldo:.0f} BIO</div>
        <div>R$ {saldo / 100:.2f}</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    "Conversão: 100 BIO = R$1,00"
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

if treino_hoje(id_participante):

    st.success(
        "✅ Treino de hoje já registrado. +10 BIO."
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

        if registrar_treino(
            id_participante,
            treino
        ):

            st.success(
                "Treino registrado! +10 BIO."
            )

            st.rerun()

# =========================================================
# FOTO
# =========================================================

st.header("📸 Foto semanal")

if foto_semana_existe(id_participante):

    st.success(
        "✅ Foto desta semana já registrada. +70 BIO."
    )

else:

    foto = st.file_uploader(
        "Enviar foto",
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
            use_container_width=True
        )

        if st.button(
            "📸 ENVIAR FOTO +70 BIO",
            use_container_width=True
        ):

            if registrar_foto(
                id_participante,
                foto.name
            ):

                st.success(
                    "Foto registrada! +70 BIO."
                )

                st.rerun()

# =========================================================
# BATTLE WITHIN
# =========================================================

st.header("🎮 Battle Within")

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
    "Fase concluída",
    min_value=1,
    max_value=40,
    step=1
)

bio_fase = recompensa_fase(fase)

st.write(
    f"Fase {fase}: **{bio_fase} BIO**"
)

if fase_concluida(
    id_participante,
    fase
):

    st.success(
        "✅ Esta fase já foi registrada."
    )

else:

    if st.button(
        f"🎮 REGISTRAR FASE {fase} +{bio_fase} BIO",
        use_container_width=True
    ):

        registrar_fase(
            id_participante,
            fase
        )

        st.success(
            f"Fase {fase} registrada!"
        )

        st.rerun()

with st.expander(
    "📋 Ver recompensas das 40 fases"
):

    for i in range(1, 41):

        valor = recompensa_fase(i)

        if fase_concluida(
            id_participante,
            i
        ):

            st.write(
                f"✅ Fase {i}: {valor} BIO"
            )

        else:

            st.write(
                f"⬜ Fase {i}: {valor} BIO"
            )

# =========================================================
# MERCADO LIVRE
# =========================================================

st.header("🛒 Mercado Livre")

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
    "é convertido em BIO."
)

# =========================================================
# COMPRA
# =========================================================

with st.expander(
    "🧾 Registrar compra"
):

    valor = st.number_input(
        "Valor da compra (R$)",
        min_value=0.0,
        step=1.0
    )

    comissao = st.number_input(
        "Comissão recebida (R$)",
        min_value=0.0,
        step=0.01
    )

    bio = comissao * 0.25

    st.write(
        f"Recompensa após validação: "
        f"**{bio:.2f} BIO**"
    )

    if st.button(
        "🧾 ENVIAR PARA VALIDAÇÃO",
        use_container_width=True
    ):

        if valor <= 0 or comissao <= 0:

            st.warning(
                "Preencha os valores corretamente."
            )

        else:

            registrar_compra(
                id_participante,
                valor,
                comissao
            )

            st.success(
                "Compra enviada para validação."
            )

# =========================================================
# SAQUE
# =========================================================

st.header("💸 Cashback")

st.write(
    f"Saldo: **{saldo:.0f} BIO = R$ {saldo / 100:.2f}**"
)

st.write(
    f"Compras qualificadas: "
    f"**{compras}/{MINIMO_COMPRAS}**"
)

if (
    saldo >= MINIMO_SAQUE
    and compras >= MINIMO_COMPRAS
):

    st.success(
        "✅ Você pode solicitar o cashback."
    )

    if st.button(
        "💸 SOLICITAR CASHBACK",
        use_container_width=True
    ):

        valor = saldo / 100

        conn = conectar()
        c = conn.cursor()

        c.execute("""
            INSERT INTO saques
            (
                participante_id,
                data,
                bio,
                valor_reais,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            id_participante,
            str(date.today()),
            saldo,
            valor,
            "Solicitado"
        ))

        conn.commit()
        conn.close()

        st.success(
            f"Solicitação enviada: "
            f"{saldo:.0f} BIO = R$ {valor:.2f}"
        )

else:

    faltam_bio = max(
        0,
        MINIMO_SAQUE - saldo
    )

    faltam_compras = max(
        0,
        MINIMO_COMPRAS - compras
    )

    st.warning(
        f"Para sacar, faltam "
        f"**{faltam_bio:.0f} BIO** e "
        f"**{faltam_compras} compra(s) qualificada(s)**."
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
### 🏋️ Treino
1 treino por dia = **10 BIO**.

### 📸 Foto semanal
1 foto por semana = **70 BIO**.

### 🎮 Battle Within
São 40 fases.

- Fases 1–10: 10 BIO
- Fases 11–20: 20 BIO
- Fases 21–30: 30 BIO
- Fases 31–40: 40 BIO

Total das 40 fases: **1.000 BIO**.

### 🛒 Mercado Livre
25% da comissão de afiliado efetivamente recebida é destinada ao participante em BIO.

### 💰 Cashback
**100 BIO = R$1,00.**

Para solicitar o cashback:

- mínimo de **5.000 BIO**
- mínimo de **2 compras qualificadas**

As compras e recompensas estão sujeitas à validação.

### 🔒 Atividades
Uma mesma atividade ou fase não pode gerar BIO novamente.
""")
