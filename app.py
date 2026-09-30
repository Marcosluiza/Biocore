import streamlit as st
import sqlite3
import hashlib
import os
from datetime import date, datetime

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="🟢",
    layout="centered"
)

DB = "biocore_novo.db"

# Links
MERCADO_LIVRE = "https://www.mercadolivre.com.br/social/sama6231844"
CORESTRYKE = "https://corestryke.com"
TRUST_WALLET = "https://trustwallet.com/"
BATTLE_WITHIN = "https://drive.google.com/uc?export=download&id=1VoOv0AacWqtweJBlmXd6awJe-bOdmfRX"

# Recompensas
BIO_TREINO = 10
BIO_FOTO = 70

# Cashback
MINIMO_SAQUE = 5000
MINIMO_COMPRAS = 2

# ============================================================
# ADMINISTRADOR
# TROQUE ESTES DOIS DADOS
# ============================================================

ADMIN_EMAIL = "admin@biocore.com"
ADMIN_SENHA = "Troque_Esta_Senha_123"


# ============================================================
# ESTILO
# ============================================================

st.markdown("""
<style>

.bio-titulo {
    font-size: 38px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 5px;
}

.biocoin {
    background: #e8f1ff;
    border: 2px solid #1976d2;
    border-radius: 15px;
    padding: 18px;
    text-align: center;
    margin: 15px 0;
}

.biocoin-numero {
    color: #1976d2;
    font-size: 32px;
    font-weight: 800;
}

.biocoin-texto {
    color: #1976d2;
    font-size: 18px;
    font-weight: 700;
}

.card {
    border: 1px solid #dddddd;
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# BANCO DE DADOS
# ============================================================

def conectar():
    return sqlite3.connect(DB)


def criar_banco():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            bio INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            atividade TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            semana TEXT NOT NULL,
            arquivo TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            fase INTEGER NOT NULL,
            bio INTEGER NOT NULL,
            UNIQUE(participante_id, fase)
        )
    """)

    cursor.execute("""
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

    cursor.execute("""
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


# ============================================================
# SENHA
# ============================================================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


# ============================================================
# PARTICIPANTES
# ============================================================

def criar_conta(nome, email, senha):

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO participantes
            (nome, email, senha, bio)
            VALUES (?, ?, ?, 0)
        """, (
            nome.strip(),
            email.strip().lower(),
            hash_senha(senha)
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def fazer_login(email, senha):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, email, bio
        FROM participantes
        WHERE email = ? AND senha = ?
    """, (
        email.strip().lower(),
        hash_senha(senha)
    ))

    usuario = cursor.fetchone()
    conn.close()

    return usuario


def obter_usuario(usuario_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, email, bio
        FROM participantes
        WHERE id = ?
    """, (usuario_id,))

    usuario = cursor.fetchone()
    conn.close()

    return usuario


# ============================================================
# TREINOS
# ============================================================

def registrar_treino(usuario_id, atividade):

    hoje = date.today().isoformat()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM treinos
        WHERE participante_id = ?
        AND data = ?
    """, (usuario_id, hoje))

    ja_registrou = cursor.fetchone()[0]

    if ja_registrou > 0:
        conn.close()
        return False, "Você já registrou um treino hoje."

    cursor.execute("""
        INSERT INTO treinos
        (participante_id, atividade, data)
        VALUES (?, ?, ?)
    """, (
        usuario_id,
        atividade,
        hoje
    ))

    cursor.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (
        BIO_TREINO,
        usuario_id
    ))

    conn.commit()
    conn.close()

    return True, f"+{BIO_TREINO} Biocoins pelo treino!"


# ============================================================
# FOTO SEMANAL
# ============================================================

def semana_atual():
    hoje = date.today()
    return f"{hoje.isocalendar().year}-W{hoje.isocalendar().week}"


def registrar_foto(usuario_id, arquivo):

    semana = semana_atual()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM fotos
        WHERE participante_id = ?
        AND semana = ?
    """, (
        usuario_id,
        semana
    ))

    ja_enviou = cursor.fetchone()[0]

    if ja_enviou > 0:
        conn.close()
        return False, "Você já enviou a foto desta semana."

    os.makedirs("uploads", exist_ok=True)

    nome_seguro = os.path.basename(arquivo.name)

    nome_final = f"{usuario_id}_{semana}_{nome_seguro}"

    caminho = os.path.join(
        "uploads",
        nome_final
    )

    with open(caminho, "wb") as f:
        f.write(arquivo.getbuffer())

    cursor.execute("""
        INSERT INTO fotos
        (participante_id, semana, arquivo)
        VALUES (?, ?, ?)
    """, (
        usuario_id,
        semana,
        caminho
    ))

    cursor.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (
        BIO_FOTO,
        usuario_id
    ))

    conn.commit()
    conn.close()

    return True, f"+{BIO_FOTO} Biocoins pela foto semanal!"


# ============================================================
# BATTLE WITHIN
# ============================================================

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


def registrar_fase(usuario_id, fase):

    if fase < 1 or fase > 40:
        return False, "A fase deve estar entre 1 e 40."

    recompensa = recompensa_fase(fase)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM fases
        WHERE participante_id = ?
        AND fase = ?
    """, (
        usuario_id,
        fase
    ))

    ja_feita = cursor.fetchone()[0]

    if ja_feita > 0:
        conn.close()
        return False, "Essa fase já foi registrada."

    cursor.execute("""
        INSERT INTO fases
        (participante_id, fase, bio)
        VALUES (?, ?, ?)
    """, (
        usuario_id,
        fase,
        recompensa
    ))

    cursor.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (
        recompensa,
        usuario_id
    ))

    conn.commit()
    conn.close()

    return True, f"+{recompensa} Biocoins pela fase {fase}!"


# ============================================================
# COMPRAS MERCADO LIVRE
# ============================================================

def registrar_compra(usuario_id, descricao, valor):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO compras
        (participante_id, descricao, valor, validada, bio, data)
        VALUES (?, ?, ?, 0, 0, ?)
    """, (
        usuario_id,
        descricao,
        valor,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def contar_compras_validadas(usuario_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM compras
        WHERE participante_id = ?
        AND validada = 1
    """, (usuario_id,))

    total = cursor.fetchone()[0]

    conn.close()

    return total


# ============================================================
# SAQUE / CASHBACK
# ============================================================

def solicitar_saque(usuario_id):

    usuario = obter_usuario(usuario_id)

    if not usuario:
        return False, "Usuário não encontrado."

    saldo = usuario[3]

    compras = contar_compras_validadas(usuario_id)

    if saldo < MINIMO_SAQUE:
        return False, "Você ainda não possui 5.000 Biocoins."

    if compras < MINIMO_COMPRAS:
        return False, "Você precisa ter pelo menos 2 compras validadas."

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM saques
        WHERE participante_id = ?
        AND status = 'Pendente'
    """, (usuario_id,))

    pendentes = cursor.fetchone()[0]

    if pendentes > 0:
        conn.close()
        return False, "Você já possui um cashback aguardando análise."

    cursor.execute("""
        INSERT INTO saques
        (participante_id, bio, valor, data, status)
        VALUES (?, ?, ?, ?, 'Pendente')
    """, (
        usuario_id,
        MINIMO_SAQUE,
        50,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return True, "Solicitação de cashback enviada."


# ============================================================
# ADMIN
# ============================================================

def validar_compra(compra_id, comissao):

    if comissao < 0:
        return False, "Comissão inválida."

    # Participante recebe 25% da comissão.
    # 100 Biocoins = R$1.
    recompensa = int(round(comissao * 0.25 * 100))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT participante_id, validada
        FROM compras
        WHERE id = ?
    """, (compra_id,))

    compra = cursor.fetchone()

    if not compra:
        conn.close()
        return False, "Compra não encontrada."

    participante_id = compra[0]
    validada = compra[1]

    if validada == 1:
        conn.close()
        return False, "Essa compra já foi validada."

    cursor.execute("""
        UPDATE compras
        SET validada = 1,
            bio = ?
        WHERE id = ?
    """, (
        recompensa,
        compra_id
    ))

    cursor.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (
        recompensa,
        participante_id
    ))

    conn.commit()
    conn.close()

    return True, f"Compra validada. +{recompensa} Biocoins."


def ajustar_biocoins(participante_id, quantidade):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT bio
        FROM participantes
        WHERE id = ?
    """, (participante_id,))

    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False

    saldo_atual = resultado[0]
    novo_saldo = saldo_atual + quantidade

    if novo_saldo < 0:
        novo_saldo = 0

    cursor.execute("""
        UPDATE participantes
        SET bio = ?
        WHERE id = ?
    """, (
        novo_saldo,
        participante_id
    ))

    conn.commit()
    conn.close()

    return True


def aprovar_saque(saque_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT participante_id, bio, status
        FROM saques
        WHERE id = ?
    """, (saque_id,))

    saque = cursor.fetchone()

    if not saque:
        conn.close()
        return False, "Saque não encontrado."

    participante_id = saque[0]
    quantidade = saque[1]
    status = saque[2]

    if status != "Pendente":
        conn.close()
        return False, "Esse saque já foi analisado."

    cursor.execute("""
        SELECT bio
        FROM participantes
        WHERE id = ?
    """, (participante_id,))

    participante = cursor.fetchone()

    if not participante:
        conn.close()
        return False, "Participante não encontrado."

    saldo = participante[0]

    if saldo < quantidade:
        cursor.execute("""
            UPDATE saques
            SET status = 'Rejeitado'
            WHERE id = ?
        """, (saque_id,))

        conn.commit()
        conn.close()

        return False, "Saldo insuficiente. Saque rejeitado."

    cursor.execute("""
        UPDATE participantes
        SET bio = bio - ?
        WHERE id = ?
    """, (
        quantidade,
        participante_id
    ))

    cursor.execute("""
        UPDATE saques
        SET status = 'Aprovado'
        WHERE id = ?
    """, (saque_id,))

    conn.commit()
    conn.close()

    return True, "Cashback aprovado."


def rejeitar_saque(saque_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE saques
        SET status = 'Rejeitado'
        WHERE id = ?
        AND status = 'Pendente'
    """, (saque_id,))

    conn.commit()

    alterou = cursor.rowcount > 0

    conn.close()

    return alterou


# ============================================================
# SESSÃO
# ============================================================

if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.usuario_id = None
    st.session_state.admin_logado = False

    st.rerun()


# ============================================================
# ÁREA DO ADMINISTRADOR
# ============================================================

def pagina_admin():

    st.markdown(
        '<div class="bio-titulo">🛠️ BioCore</div>',
        unsafe_allow_html=True
    )

    st.subheader("Painel do Administrador")

    if st.button("🚪 Sair do administrador", key="admin_logout"):
        logout()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM participantes")
    total_participantes = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(bio), 0) FROM participantes")
    total_biocoins = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM compras
        WHERE validada = 0
    """)
    compras_pendentes = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM saques
        WHERE status = 'Pendente'
    """)
    saques_pendentes = cursor.fetchone()[0]

    conn.close()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Participantes", total_participantes)

    with col2:
        st.metric("Biocoins", total_biocoins)

    col3, col4 = st.columns(2)

    with col3:
        st.metric("Compras pendentes", compras_pendentes)

    with col4:
        st.metric("Cashbacks pendentes", saques_pendentes)

    abas = st.tabs([
        "👥 Participantes",
        "🛒 Compras",
        "💰 Cashbacks",
        "🏋️ Atividades"
    ])

    # --------------------------------------------------------
    # PARTICIPANTES
    # --------------------------------------------------------

    with abas[0]:

        st.subheader("Participantes")

        conn = conectar()

        participantes = conn.execute("""
            SELECT id, nome, email, bio
            FROM participantes
            ORDER BY nome
        """).fetchall()

        conn.close()

        if not participantes:
            st.info("Nenhum participante cadastrado.")

        else:

            for participante in participantes:

                pid = participante[0]
                nome = participante[1]
                email = participante[2]
                saldo = participante[3]

                with st.expander(
                    f"👤 {nome} — {saldo} Biocoins"
                ):

                    st.write(f"**E-mail:** {email}")
                    st.write(f"**ID:** {pid}")

                    st.markdown(
                        f"""
                        <div class="biocoin">
                            <div class="biocoin-numero">
                                🪙 {saldo}
                            </div>
                            <div class="biocoin-texto">
                                Biocoins
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    quantidade = st.number_input(
                        "Quantidade de Biocoins para ajustar",
                        min_value=-1000000,
                        max_value=1000000,
                        value=0,
                        step=10,
                        key=f"ajuste_valor_{pid}"
                    )

                    if st.button(
                        "Aplicar ajuste",
                        key=f"ajuste_botao_{pid}"
                    ):

                        ajustar_biocoins(
                            pid,
                            quantidade
                        )

                        st.success(
                            "Saldo atualizado."
                        )

                        st.rerun()

    # --------------------------------------------------------
    # COMPRAS
    # --------------------------------------------------------

    with abas[1]:

        st.subheader("Compras do Mercado Livre")

        conn = conectar()

        compras = conn.execute("""
            SELECT
                compras.id,
                participantes.nome,
                participantes.email,
                compras.descricao,
                compras.valor,
                compras.validada,
                compras.bio,
                compras.data
            FROM compras
            JOIN participantes
            ON participantes.id = compras.participante_id
            ORDER BY compras.id DESC
        """).fetchall()

        conn.close()

        if not compras:
            st.info("Nenhuma compra registrada.")

        for compra in compras:

            compra_id = compra[0]
            nome = compra[1]
            email = compra[2]
            descricao = compra[3]
            valor = compra[4]
            validada = compra[5]
            recompensa = compra[6]
            data_compra = compra[7]

            with st.expander(
                f"🛒 {nome} — R$ {valor:.2f}"
            ):

                st.write(f"**E-mail:** {email}")
                st.write(f"**Produto:** {descricao}")
                st.write(f"**Valor:** R$ {valor:.2f}")
                st.write(f"**Data:** {data_compra}")

                if validada:

                    st.success(
                        f"Validada — {recompensa} Biocoins"
                    )

                else:

                    st.warning(
                        "Aguardando validação"
                    )

                    comissao = st.number_input(
                        "Comissão recebida pelo BioCore (R$)",
                        min_value=0.0,
                        step=0.01,
                        value=0.0,
                        key=f"comissao_{compra_id}"
                    )

                    if st.button(
                        "✅ Validar compra",
                        key=f"validar_compra_{compra_id}"
                    ):

                        sucesso, mensagem = validar_compra(
                            compra_id,
                            comissao
                        )

                        if sucesso:
                            st.success(mensagem)
                        else:
                            st.error(mensagem)

                        st.rerun()

    # --------------------------------------------------------
    # CASHBACK
    # --------------------------------------------------------

    with abas[2]:

        st.subheader("Solicitações de Cashback")

        conn = conectar()

        saques = conn.execute("""
            SELECT
                saques.id,
                participantes.nome,
                participantes.email,
                saques.bio,
                saques.valor,
                saques.data,
                saques.status
            FROM saques
            JOIN participantes
            ON participantes.id = saques.participante_id
            ORDER BY saques.id DESC
        """).fetchall()

        conn.close()

        if not saques:
            st.info("Nenhuma solicitação.")

        for saque in saques:

            saque_id = saque[0]
            nome = saque[1]
            email = saque[2]
            quantidade = saque[3]
            valor = saque[4]
            data_saque = saque[5]
            status = saque[6]

            with st.expander(
                f"💰 {nome} — R$ {valor:.2f} — {status}"
            ):

                st.write(f"**E-mail:** {email}")
                st.write(f"**Biocoins:** {quantidade}")
                st.write(f"**Valor:** R$ {valor:.2f}")
                st.write(f"**Data:** {data_saque}")
                st.write(f"**Status:** {status}")

                if status == "Pendente":

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "✅ Aprovar",
                            key=f"aprovar_saque_{saque_id}"
                        ):

                            sucesso, mensagem = aprovar_saque(
                                saque_id
                            )

                            if sucesso:
                                st.success(mensagem)
                            else:
                                st.error(mensagem)

                            st.rerun()

                    with col2:

                        if st.button(
                            "❌ Rejeitar",
                            key=f"rejeitar_saque_{saque_id}"
                        ):

                            rejeitar_saque(
                                saque_id
                            )

                            st.warning(
                                "Cashback rejeitado."
                            )

                            st.rerun()

    # --------------------------------------------------------
    # ATIVIDADES
    # --------------------------------------------------------

    with abas[3]:

        st.subheader("Atividades dos participantes")

        st.markdown("### 🏋️ Treinos")

        conn = conectar()

        treinos = conn.execute("""
            SELECT
                participantes.nome,
                treinos.atividade,
                treinos.data
            FROM treinos
            JOIN participantes
            ON participantes.id = treinos.participante_id
            ORDER BY treinos.id DESC
        """).fetchall()

        conn.close()

        if treinos:
            for treino in treinos:
                st.write(
                    f"**{treino[0]}** — "
                    f"{treino[1]} — "
                    f"{treino[2]}"
                )
        else:
            st.info("Nenhum treino registrado.")

        st.markdown("### 🎮 Battle Within")

        conn = conectar()

        fases = conn.execute("""
            SELECT
                participantes.nome,
                fases.fase,
                fases.bio
            FROM fases
            JOIN participantes
            ON participantes.id = fases.participante_id
            ORDER BY fases.id DESC
        """).fetchall()

        conn.close()

        if fases:
            for fase in fases:
                st.write(
                    f"**{fase[0]}** — "
                    f"Fase {fase[1]} — "
                    f"+{fase[2]} Biocoins"
                )
        else:
            st.info("Nenhuma fase registrada.")

        st.markdown("### 📸 Fotos")

        conn = conectar()

        fotos = conn.execute("""
            SELECT
                participantes.nome,
                fotos.semana,
                fotos.arquivo
            FROM fotos
            JOIN participantes
            ON participantes.id = fotos.participante_id
            ORDER BY fotos.id DESC
        """).fetchall()

        conn.close()

        if fotos:

            for foto in fotos:

                st.write(
                    f"**{foto[0]}** — {foto[1]}"
                )

                caminho = foto[2]

                if os.path.exists(caminho):

                    st.image(
                        caminho,
                        width=300
                    )

        else:
            st.info("Nenhuma foto enviada.")


# ============================================================
# ÁREA DO PARTICIPANTE
# ============================================================

def pagina_participante():

    usuario = obter_usuario(
        st.session_state.usuario_id
    )

    if not usuario:
        logout()

    usuario_id = usuario[0]
    nome = usuario[1]
    email = usuario[2]
    saldo = usuario[3]

    st.markdown(
        '<div class="bio-titulo">🟢 BioCore</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"Olá, **{nome}**!"
    )

    # --------------------------------------------------------
    # SALDO
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="biocoin">
            <div class="biocoin-numero">
                🪙 {saldo}
            </div>
            <div class="biocoin-texto">
                Biocoins
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🚪 Sair",
        key="participante_logout"
    ):
        logout()

    # --------------------------------------------------------
    # LINKS
    # --------------------------------------------------------

    st.subheader("Acessos")

    col1, col2 = st.columns(2)

    with col1:

        st.link_button(
            "🛍️ CoreStryke",
            CORESTRYKE,
            use_container_width=True
        )

    with col2:

        st.link_button(
            "🛒 Mercado Livre",
            MERCADO_LIVRE,
            use_container_width=True
        )

    col3, col4 = st.columns(2)

    with col3:

        st.link_button(
            "👛 Trust Wallet",
            TRUST_WALLET,
            use_container_width=True
        )

    with col4:

        st.link_button(
            "🎮 Battle Within",
            BATTLE_WITHIN,
            use_container_width=True
        )

    # --------------------------------------------------------
    # TREINO
    # --------------------------------------------------------

    st.divider()

    st.subheader("🏋️ Registrar treino")

    atividades = [
        "Peito / Ombro / Tríceps",
        "Dorsal / Bíceps",
        "Quadríceps / Glúteo / Panturrilha",
        "Perna completo",
        "Abdômen",
        "Peso corporal",
        "Corrida",
        "Futebol"
    ]

    atividade = st.selectbox(
        "Escolha a atividade",
        atividades,
        key="atividade_treino"
    )

    if st.button(
        "🏋️ Registrar treino",
        key="botao_registrar_treino",
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

    # --------------------------------------------------------
    # FOTO
    # --------------------------------------------------------

    st.divider()

    st.subheader("📸 Foto semanal")

    st.write(
        f"Você recebe **+{BIO_FOTO} Biocoins** "
        "por uma foto por semana."
    )

    arquivo = st.file_uploader(
        "Enviar foto",
        type=["jpg", "jpeg", "png"],
        key="foto_semanal"
    )

    if arquivo:

        st.image(
            arquivo,
            caption="Foto selecionada",
            width=300
        )

        if st.button(
            "📸 Enviar foto",
            key="botao_enviar_foto",
            use_container_width=True
        ):

            sucesso, mensagem = registrar_foto(
                usuario_id,
                arquivo
            )

            if sucesso:
                st.success(mensagem)
                st.rerun()
            else:
                st.warning(mensagem)

    # --------------------------------------------------------
    # BATTLE WITHIN
    # --------------------------------------------------------

    st.divider()

    st.subheader("🎮 Battle Within")

    st.write(
        "Complete as fases e registre cada fase concluída."
    )

    fase = st.number_input(
        "Número da fase",
        min_value=1,
        max_value=40,
        value=1,
        step=1,
        key="numero_fase"
    )

    recompensa = recompensa_fase(fase)

    st.info(
        f"Fase {fase}: +{recompensa} Biocoins"
    )

    if st.button(
        "🎮 Registrar fase concluída",
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

    # --------------------------------------------------------
    # MERCADO LIVRE
    # --------------------------------------------------------

    st.divider()

    st.subheader("🛒 Compra no Mercado Livre")

    st.write(
        "Faça sua compra pelo link do BioCore "
        "e depois envie os dados da compra para validação."
    )

    st.link_button(
        "🛒 Abrir Mercado Livre",
        MERCADO_LIVRE,
        use_container_width=True
    )

    descricao = st.text_input(
        "O que você comprou?",
        key="descricao_compra"
    )

    valor = st.number_input(
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

        if descricao.strip() == "":
            st.warning(
                "Informe o produto."
            )

        elif valor <= 0:
            st.warning(
                "Informe o valor da compra."
            )

        else:

            registrar_compra(
                usuario_id,
                descricao,
                valor
            )

            st.success(
                "Compra enviada para validação."
            )

    # --------------------------------------------------------
    # CASHBACK
    # --------------------------------------------------------

    st.divider()

    st.subheader("💰 Cashback")

    compras = contar_compras_validadas(
        usuario_id
    )

    st.write(
        f"Compras validadas: **{compras}**"
    )

    st.write(
        "5.000 Biocoins = R$50 de cashback."
    )

    if saldo >= MINIMO_SAQUE:
        st.success(
            "Você atingiu 5.000 Biocoins."
        )
    else:
        faltam = MINIMO_SAQUE - saldo

        st.info(
            f"Faltam {faltam} Biocoins para atingir 5.000."
        )

    if compras >= MINIMO_COMPRAS:
        st.success(
            "Você possui pelo menos 2 compras validadas."
        )
    else:
        faltam_compras = MINIMO_COMPRAS - compras

        st.info(
            f"Faltam {faltam_compras} compra(s) validada(s)."
        )

    if st.button(
        "💰 Solicitar R$50 de cashback",
        key="botao_cashback",
        use_container_width=True
    ):

        sucesso, mensagem = solicitar_saque(
            usuario_id
        )

        if sucesso:
            st.success(mensagem)
            st.rerun()
        else:
            st.warning(mensagem)

    # --------------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------------

    st.divider()

    st.subheader("📋 Meu histórico")

    aba1, aba2, aba3 = st.tabs([
        "🏋️ Treinos",
        "🎮 Fases",
        "💰 Cashback"
    ])

    with aba1:

        conn = conectar()

        registros = conn.execute("""
            SELECT atividade, data
            FROM treinos
            WHERE participante_id = ?
            ORDER BY id DESC
        """, (usuario_id,)).fetchall()

        conn.close()

        if registros:

            for registro in registros:

                st.write(
                    f"🏋️ {registro[0]} — {registro[1]}"
                )

        else:
            st.info(
                "Nenhum treino registrado."
            )

    with aba2:

        conn = conectar()

        registros = conn.execute("""
            SELECT fase, bio
            FROM fases
            WHERE participante_id = ?
            ORDER BY fase
        """, (usuario_id,)).fetchall()

        conn.close()

        if registros:

            for registro in registros:

                st.write(
                    f"🎮 Fase {registro[0]} "
                    f"— +{registro[1]} Biocoins"
                )

        else:
            st.info(
                "Nenhuma fase registrada."
            )

    with aba3:

        conn = conectar()

        registros = conn.execute("""
            SELECT bio, valor, data, status
            FROM saques
            WHERE participante_id = ?
            ORDER BY id DESC
        """, (usuario_id,)).fetchall()

        conn.close()

        if registros:

            for registro in registros:

                st.write(
                    f"💰 {registro[0]} Biocoins "
                    f"— R$ {registro[1]:.2f} "
                    f"— {registro[3]} "
                    f"— {registro[2]}"
                )

        else:
            st.info(
                "Nenhuma solicitação de cashback."
            )

    # --------------------------------------------------------
    # REGRAS
    # --------------------------------------------------------

    st.divider()

    with st.expander("📜 Regras do BioCore"):

        st.markdown("""
### 🪙 Biocoins

- Treino: **+10 Biocoins**
- Foto semanal: **+70 Biocoins**
- Máximo de 1 treino por dia.
- Máximo de 1 foto por semana.

### 🎮 Battle Within

- Fases 1–10: **10 Biocoins por fase**
- Fases 11–20: **20 Biocoins por fase**
- Fases 21–30: **30 Biocoins por fase**
- Fases 31–40: **40 Biocoins por fase**
- Cada fase só pode gerar recompensa uma vez.
- As 40 fases totalizam **1.000 Biocoins**.

### 🛒 Mercado Livre

A compra precisa ser feita pelo link do BioCore.

Depois, a compra será analisada e validada.

O participante recebe **25% da comissão efetivamente recebida pelo BioCore**, convertida em Biocoins.

### 💰 Cashback

- **5.000 Biocoins = R$50**
- É necessário ter pelo menos **2 compras validadas**.
- O pedido passa por análise administrativa.
        """)


# ============================================================
# TELA DE LOGIN / CADASTRO
# ============================================================

def pagina_login():

    st.markdown(
        '<div class="bio-titulo">🟢 BioCore</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Treine, participe e acumule **Biocoins**."
    )

    entrar, cadastro, administrador = st.tabs([
        "Entrar",
        "Criar conta",
        "Administrador"
    ])

    # ========================================================
    # ENTRAR
    # ========================================================

    with entrar:

        email = st.text_input(
            "E-mail",
            key="campo_email_login"
        )

        senha = st.text_input(
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
                email,
                senha
            )

            if usuario:

                st.session_state.usuario_id = usuario[0]

                st.rerun()

            else:

                st.error(
                    "E-mail ou senha incorretos."
                )

    # ========================================================
    # CADASTRO
    # ========================================================

    with cadastro:

        nome = st.text_input(
            "Nome",
            key="campo_nome_cadastro"
        )

        email = st.text_input(
            "E-mail",
            key="campo_email_cadastro"
        )

        senha = st.text_input(
            "Senha",
            type="password",
            key="campo_senha_cadastro"
        )

        confirmar = st.text_input(
            "Confirmar senha",
            type="password",
            key="campo_confirmar_cadastro"
        )

        if st.button(
            "Criar conta",
            key="botao_cadastro",
            use_container_width=True
        ):

            if not nome.strip():
                st.warning(
                    "Informe seu nome."
                )

            elif not email.strip():
                st.warning(
                    "Informe seu e-mail."
                )

            elif not senha:
                st.warning(
                    "Informe uma senha."
                )

            elif senha != confirmar:
                st.error(
                    "As senhas não são iguais."
                )

            else:

                sucesso = criar_conta(
                    nome,
                    email,
                    senha
                )

                if sucesso:

                    st.success(
                        "Conta criada! Agora você pode entrar."
                    )

                else:

                    st.error(
                        "Esse e-mail já está cadastrado."
                    )

    # ========================================================
    # ADMIN
    # ========================================================

    with administrador:

        st.subheader("🛠️ Acesso administrativo")

        admin_email = st.text_input(
            "E-mail do administrador",
            key="campo_admin_email"
        )

        admin_senha = st.text_input(
            "Senha do administrador",
            type="password",
            key="campo_admin_senha"
        )

        if st.button(
            "Entrar como administrador",
            key="botao_admin_login",
            use_container_width=True
        ):

            if (
                admin_email.strip().lower()
                == ADMIN_EMAIL.lower()
                and admin_senha
                == ADMIN_SENHA
            ):

                st.session_state.admin_logado = True

                st.rerun()

            else:

                st.error(
                    "Dados administrativos incorretos."
                )


# ============================================================
# ROTEAMENTO
# ============================================================

if st.session_state.admin_logado:

    pagina_admin()

elif st.session_state.usuario_id is not None:

    pagina_participante()

else:

    pagina_login()
