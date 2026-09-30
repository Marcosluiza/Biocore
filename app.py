import streamlit as st
import sqlite3
import hashlib
from datetime import date, datetime

# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="🟢",
    layout="centered"
)

DB = "biocore_novo.db"

MERCADO_LIVRE = "https://www.mercadolivre.com.br/social/sama6231844"
CORESTRYKE = "https://corestryke.com"
TRUST_WALLET = "https://trustwallet.com/"
BATTLE_WITHIN = "https://drive.google.com/uc?export=download&id=1VoOv0AacWqtweJBlmXd6awJe-bOdmfRX"

BIO_TREINO = 10
BIO_FOTO = 70
MINIMO_SAQUE = 5000
MINIMO_COMPRAS = 2


# =========================================================
# BANCO
# =========================================================

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

    c.execute("""
        CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            atividade TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            semana TEXT NOT NULL,
            arquivo TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            fase INTEGER NOT NULL,
            bio INTEGER NOT NULL,
            UNIQUE(participante_id, fase)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            validada INTEGER DEFAULT 0,
            bio INTEGER DEFAULT 0,
            data TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS saques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            bio INTEGER NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            status TEXT DEFAULT 'Pendente'
        )
    """)

    conn.commit()
    conn.close()


criar_banco()


# =========================================================
# SEGURANÇA
# =========================================================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


# =========================================================
# CONTA
# =========================================================

def criar_conta(nome, email, senha):
    conn = conectar()
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO participantes
            (nome, email, senha, bio)
            VALUES (?, ?, ?, 0)
        """, (
            nome.strip(),
            email.strip().lower(),
            hash_senha(senha)
        ))

        conn.commit()

        return True, "Conta criada com sucesso!"

    except sqlite3.IntegrityError:
        return False, "Este e-mail já está cadastrado."

    finally:
        conn.close()


def fazer_login(email, senha):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT id, nome
        FROM participantes
        WHERE email = ? AND senha = ?
    """, (
        email.strip().lower(),
        hash_senha(senha)
    ))

    resultado = c.fetchone()

    conn.close()

    return resultado


def obter_usuario(usuario_id):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT id, nome, email, bio
        FROM participantes
        WHERE id = ?
    """, (usuario_id,))

    resultado = c.fetchone()

    conn.close()

    return resultado


# =========================================================
# TREINO
# =========================================================

def treino_hoje(usuario_id):
    hoje = date.today().isoformat()

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*)
        FROM treinos
        WHERE participante_id = ?
        AND data = ?
    """, (usuario_id, hoje))

    resultado = c.fetchone()[0]

    conn.close()

    return resultado > 0


def registrar_treino(usuario_id, atividade):

    if treino_hoje(usuario_id):
        return False, "Você já registrou um treino hoje."

    hoje = date.today().isoformat()

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO treinos
        (participante_id, atividade, data)
        VALUES (?, ?, ?)
    """, (
        usuario_id,
        atividade,
        hoje
    ))

    c.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (
        BIO_TREINO,
        usuario_id
    ))

    conn.commit()
    conn.close()

    return True, "Treino registrado! +10 BIO"


# =========================================================
# FOTO
# =========================================================

def semana_atual():
    return date.today().strftime("%Y-%W")


def foto_existe(usuario_id):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*)
        FROM fotos
        WHERE participante_id = ?
        AND semana = ?
    """, (
        usuario_id,
        semana_atual()
    ))

    resultado = c.fetchone()[0]

    conn.close()

    return resultado > 0


def registrar_foto(usuario_id, nome_arquivo):

    if foto_existe(usuario_id):
        return False, "Você já enviou a foto desta semana."

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO fotos
        (participante_id, semana, arquivo)
        VALUES (?, ?, ?)
    """, (
        usuario_id,
        semana_atual(),
        nome_arquivo
    ))

    c.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (
        BIO_FOTO,
        usuario_id
    ))

    conn.commit()
    conn.close()

    return True, "Foto registrada! +70 BIO"


# =========================================================
# BATTLE WITHIN
# =========================================================

def recompensa_fase(fase):

    if 1 <= fase <= 10:
        return 10

    if 11 <= fase <= 20:
        return 20

    if 21 <= fase <= 30:
        return 30

    if 31 <= fase <= 40:
        return 40

    return 0


def fase_existe(usuario_id, fase):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*)
        FROM fases
        WHERE participante_id = ?
        AND fase = ?
    """, (
        usuario_id,
        fase
    ))

    resultado = c.fetchone()[0]

    conn.close()

    return resultado > 0


def registrar_fase(usuario_id, fase):

    recompensa = recompensa_fase(fase)

    if recompensa == 0:
        return False, "Fase inválida."

    if fase_existe(usuario_id, fase):
        return False, "Essa fase já foi registrada."

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO fases
        (participante_id, fase, bio)
        VALUES (?, ?, ?)
    """, (
        usuario_id,
        fase,
        recompensa
    ))

    c.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (
        recompensa,
        usuario_id
    ))

    conn.commit()
    conn.close()

    return True, f"Fase {fase} concluída! +{recompensa} BIO"


# =========================================================
# COMPRAS
# =========================================================

def registrar_compra(usuario_id, descricao, valor):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO compras
        (participante_id, descricao, valor, validada, bio, data)
        VALUES (?, ?, ?, 0, 0, ?)
    """, (
        usuario_id,
        descricao,
        valor,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def compras_qualificadas(usuario_id):

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*)
        FROM compras
        WHERE participante_id = ?
        AND validada = 1
    """, (usuario_id,))

    resultado = c.fetchone()[0]

    conn.close()

    return resultado


# =========================================================
# SAQUE
# =========================================================

def solicitar_saque(usuario_id, bio):

    valor = bio / 100

    conn = conectar()
    c = conn.cursor()

    c.execute("""
        INSERT INTO saques
        (participante_id, bio, valor, data, status)
        VALUES (?, ?, ?, ?, 'Pendente')
    """, (
        usuario_id,
        bio,
        valor,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


# =========================================================
# SESSÃO
# =========================================================

if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None


# =========================================================
# LOGIN / CADASTRO
# =========================================================

if not st.session_state.logado:

    st.title("🟢 BioCore")

    st.subheader(
        "Treino • Atividade Física • Recompensas"
    )

    aba_entrar, aba_cadastro = st.tabs([
        "Entrar",
        "Criar conta"
    ])

    # -----------------------------------------------------
    # ENTRAR
    # -----------------------------------------------------

    with aba_entrar:

        st.markdown("### 🔐 Entrar")

        email_login = st.text_input(
            "E-mail",
            key="campo_email_login"
        )

        senha_login = st.text_input(
            "Senha",
            type="password",
            key="campo_senha_login"
        )

        if st.button(
            "Entrar",
            key="botao_login",
            use_container_width=True
        ):

            usuario = fazer_login(
                email_login,
                senha_login
            )

            if usuario:

                st.session_state.logado = True
                st.session_state.usuario_id = usuario[0]

                st.rerun()

            else:

                st.error(
                    "E-mail ou senha incorretos."
                )

    # -----------------------------------------------------
    # CADASTRO
    # -----------------------------------------------------

    with aba_cadastro:

        st.markdown("### 👤 Criar conta")

        nome_cadastro = st.text_input(
            "Nome",
            key="campo_nome_cadastro"
        )

        email_cadastro = st.text_input(
            "E-mail",
            key="campo_email_cadastro"
        )

        senha_cadastro = st.text_input(
            "Senha",
            type="password",
            key="campo_senha_cadastro"
        )

        confirmar_cadastro = st.text_input(
            "Confirmar senha",
            type="password",
            key="campo_confirmar_cadastro"
        )

        if st.button(
            "Criar minha conta",
            key="botao_cadastro",
            use_container_width=True
        ):

            if not nome_cadastro:
                st.error("Digite seu nome.")

            elif not email_cadastro:
                st.error("Digite seu e-mail.")

            elif not senha_cadastro:
                st.error("Digite uma senha.")

            elif senha_cadastro != confirmar_cadastro:
                st.error("As senhas não são iguais.")

            elif len(senha_cadastro) < 6:
                st.error(
                    "A senha precisa ter pelo menos 6 caracteres."
                )

            else:

                sucesso, mensagem = criar_conta(
                    nome_cadastro,
                    email_cadastro,
                    senha_cadastro
                )

                if sucesso:

                    st.success(mensagem)

                    st.info(
                        "Agora entre usando seu e-mail e senha."
                    )

                else:

                    st.error(mensagem)

    st.divider()

    st.markdown("""
### 🟢 Como funciona

🏋️ Registre seus treinos  
📸 Envie sua foto semanal  
🎮 Jogue Battle Within  
🛒 Compre pelo Mercado Livre  
🪙 Acumule BIO  
💰 Solicite cashback quando cumprir as regras
""")

    st.stop()


# =========================================================
# ÁREA LOGADA
# =========================================================

usuario = obter_usuario(
    st.session_state.usuario_id
)

if not usuario:

    st.session_state.logado = False
    st.session_state.usuario_id = None
    st.rerun()


usuario_id = usuario[0]
nome = usuario[1]
email = usuario[2]
bio = usuario[3]

valor_reais = bio / 100
compras = compras_qualificadas(usuario_id)


# =========================================================
# CABEÇALHO
# =========================================================

st.title("🟢 BioCore")

st.write(
    f"Olá, **{nome}**!"
)

if st.button(
    "Sair",
    key="botao_sair"
):

    st.session_state.logado = False
    st.session_state.usuario_id = None

    st.rerun()


# =========================================================
# SALDO
# =========================================================

st.divider()

st.subheader("🪙 Seu saldo")

coluna1, coluna2 = st.columns(2)

with coluna1:

    st.metric(
        "BIO",
        f"{bio:,}".replace(",", ".")
    )

with coluna2:

    st.metric(
        "Valor",
        f"R$ {valor_reais:,.2f}".replace(
            ",", "X"
        ).replace(
            ".", ","
        ).replace(
            "X", "."
        )
    )

st.caption("100 BIO = R$ 1,00")


# =========================================================
# TREINO
# =========================================================

st.divider()

st.subheader("🏋️ Registrar treino")

atividade = st.selectbox(
    "Escolha a atividade",
    [
        "Peito / Ombro / Tríceps",
        "Dorsal / Bíceps",
        "Quadríceps / Glúteo / Panturrilha",
        "Perna completa",
        "Abdômen",
        "Peso corporal",
        "Corrida",
        "Futebol"
    ],
    key="atividade_treino"
)

if st.button(
    "Registrar treino +10 BIO",
    key="botao_treino",
    use_container_width=True
):

    sucesso, mensagem = registrar_treino(
        usuario_id,
        atividade
    )

    if sucesso:

        st.success(mensagem)
        st.rerun()

    else:

        st.warning(mensagem)


# =========================================================
# FOTO
# =========================================================

st.divider()

st.subheader("📸 Foto semanal")

st.write(
    "Envie uma foto do seu treino."
)

foto = st.file_uploader(
    "Escolha sua foto",
    type=["jpg", "jpeg", "png"],
    key="upload_foto"
)

if foto:

    if st.button(
        "Registrar foto +70 BIO",
        key="botao_foto",
        use_container_width=True
    ):

        sucesso, mensagem = registrar_foto(
            usuario_id,
            foto.name
        )

        if sucesso:

            st.success(mensagem)
            st.rerun()

        else:

            st.warning(mensagem)


# =========================================================
# BATTLE WITHIN
# =========================================================

st.divider()

st.subheader("🎮 Battle Within")

st.write(
    "O Battle Within possui 40 fases."
)

st.link_button(
    "⬇️ Baixar Battle Within",
    BATTLE_WITHIN,
    use_container_width=True
)

fase = st.number_input(
    "Fase concluída",
    min_value=1,
    max_value=40,
    value=1,
    step=1,
    key="numero_fase"
)

recompensa = recompensa_fase(fase)

st.info(
    f"Essa fase vale **{recompensa} BIO**."
)

if st.button(
    f"Registrar fase {fase}",
    key="botao_fase",
    use_container_width=True
):

    sucesso, mensagem = registrar_fase(
        usuario_id,
        fase
    )

    if sucesso:

        st.success(mensagem)
        st.rerun()

    else:

        st.warning(mensagem)

st.markdown("### Recompensas das fases")

st.write("Fases 1–10 → 10 BIO cada")
st.write("Fases 11–20 → 20 BIO cada")
st.write("Fases 21–30 → 30 BIO cada")
st.write("Fases 31–40 → 40 BIO cada")

st.caption("Total das 40 fases: 1.000 BIO")


# =========================================================
# MERCADO LIVRE
# =========================================================

st.divider()

st.subheader("🛒 Mercado Livre")

st.write(
    "Use o link abaixo para realizar suas compras."
)

st.link_button(
    "🛒 Abrir Mercado Livre",
    MERCADO_LIVRE,
    use_container_width=True
)

st.info(
    "Nas compras qualificadas, o participante recebe BIO "
    "correspondente a 25% da comissão de afiliado "
    "efetivamente recebida e validada."
)

descricao_compra = st.text_input(
    "Produto comprado",
    key="descricao_compra"
)

valor_compra = st.number_input(
    "Valor da compra (R$)",
    min_value=0.0,
    step=1.0,
    key="valor_compra"
)

if st.button(
    "Enviar compra para validação",
    key="botao_compra",
    use_container_width=True
):

    if not descricao_compra:

        st.warning(
            "Digite o produto comprado."
        )

    elif valor_compra <= 0:

        st.warning(
            "Digite o valor da compra."
        )

    else:

        registrar_compra(
            usuario_id,
            descricao_compra,
            valor_compra
        )

        st.success(
            "Compra enviada para validação."
        )


# =========================================================
# SAQUE
# =========================================================

st.divider()

st.subheader("💰 Cashback")

st.write(
    "Regras para solicitar cashback:"
)

st.write(
    "🪙 Mínimo: **5.000 BIO**"
)

st.write(
    "🛒 Mínimo: **2 compras qualificadas validadas**"
)

st.write(
    f"Suas compras qualificadas: **{compras}**"
)

if bio >= MINIMO_SAQUE and compras >= MINIMO_COMPRAS:

    st.success(
        f"Você pode solicitar R$ {valor_reais:.2f}."
    )

    if st.button(
        "Solicitar cashback",
        key="botao_saque",
        use_container_width=True
    ):

        solicitar_saque(
            usuario_id,
            bio
        )

        st.success(
            "Solicitação enviada para análise."
        )

else:

    st.info(
        "Você ainda não atingiu os requisitos "
        "para solicitar cashback."
    )


# =========================================================
# CORESTRYKE
# =========================================================

st.divider()

st.subheader("🛍️ CoreStryke")

st.write(
    "Acesse a loja."
)

st.link_button(
    "Abrir CoreStryke",
    CORESTRYKE,
    use_container_width=True
)


# =========================================================
# TRUST WALLET
# =========================================================

st.divider()

st.subheader("👛 Trust Wallet")

st.write(
    "Acesse sua carteira."
)

st.link_button(
    "Abrir Trust Wallet",
    TRUST_WALLET,
    use_container_width=True
)


# =========================================================
# REGRAS
# =========================================================

st.divider()

with st.expander("📜 Regras do BioCore"):

    st.markdown("""
### 🏋️ Treino

• Máximo de 1 treino por dia.  
• Cada treino vale **10 BIO**.

### 📸 Foto semanal

• Máximo de 1 foto por semana.  
• Cada foto vale **70 BIO**.

### 🎮 Battle Within

• São 40 fases.  
• Cada fase só pode gerar recompensa uma vez.

• Fases 1–10: **10 BIO cada**  
• Fases 11–20: **20 BIO cada**  
• Fases 21–30: **30 BIO cada**  
• Fases 31–40: **40 BIO cada**

Total possível: **1.000 BIO**.

### 🛒 Mercado Livre

A compra deve ser feita pelo link de afiliado do BioCore.

A recompensa depende da comissão efetivamente recebida e validada.

O participante recebe **25% da comissão em BIO**.

### 💰 Cashback

• 5.000 BIO = R$ 50,00  
• 100 BIO = R$ 1,00  
• Necessário ter pelo menos 2 compras qualificadas validadas.

A solicitação de cashback passa por validação.
""")


st.divider()

st.caption(
    "BioCore • Treino, atividade física e recompensas"
)
