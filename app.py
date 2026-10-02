import streamlit as st
import requests
import hashlib
import secrets
import binascii
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="💪",
    layout="centered"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

BUCKET = "Comprovacoes"

FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

# Temporário. Depois podemos colocar nos Secrets.
ADMIN_PASSWORD = "1234"


# =========================================================
# SESSÃO
# =========================================================

if "participante" not in st.session_state:
    st.session_state.participante = None

if "admin" not in st.session_state:
    st.session_state.admin = False


# =========================================================
# SUPABASE
# =========================================================

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


def supabase_get(tabela, params=None):

    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    try:

        resposta = requests.get(
            url,
            headers=HEADERS,
            params=params or {},
            timeout=30
        )

        if resposta.status_code >= 400:
            st.error(
                f"Erro ao consultar o banco: {resposta.text}"
            )
            return []

        return resposta.json()

    except Exception as erro:

        st.error(
            f"Erro de conexão: {erro}"
        )

        return []


def supabase_insert(tabela, dados):

    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    headers = {
        **HEADERS,
        "Prefer": "return=representation"
    }

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json=dados,
            timeout=30
        )

        if resposta.status_code >= 400:

            st.error(
                f"Erro ao salvar: {resposta.text}"
            )

            return None

        try:
            return resposta.json()
        except Exception:
            return True

    except Exception as erro:

        st.error(
            f"Erro de conexão: {erro}"
        )

        return None


def supabase_update(tabela, filtros, dados):

    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    headers = {
        **HEADERS,
        "Prefer": "return=representation"
    }

    try:

        resposta = requests.patch(
            url,
            headers=headers,
            params=filtros,
            json=dados,
            timeout=30
        )

        if resposta.status_code >= 400:

            st.error(
                f"Erro ao atualizar: {resposta.text}"
            )

            return None

        try:
            return resposta.json()
        except Exception:
            return True

    except Exception as erro:

        st.error(
            f"Erro de conexão: {erro}"
        )

        return None


# =========================================================
# SENHAS
# =========================================================

def criar_hash_senha(senha):

    salt = secrets.token_bytes(16)

    senha_hash = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt,
        200000
    )

    return (
        binascii.hexlify(salt).decode()
        + "$"
        + binascii.hexlify(senha_hash).decode()
    )


def verificar_senha(senha, senha_hash):

    try:

        salt_hex, hash_hex = senha_hash.split("$")

        salt = binascii.unhexlify(salt_hex)

        novo_hash = hashlib.pbkdf2_hmac(
            "sha256",
            senha.encode("utf-8"),
            salt,
            200000
        )

        return secrets.compare_digest(
            binascii.hexlify(novo_hash).decode(),
            hash_hex
        )

    except Exception:

        return False


# =========================================================
# HORÁRIO
# =========================================================

def agora_brasil():

    return datetime.now(FUSO_BRASIL)


def inicio_dia_brasil():

    agora = agora_brasil()

    return agora.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )


def inicio_dia_utc():

    return inicio_dia_brasil().astimezone(
        timezone.utc
    ).isoformat()


def inicio_proximo_dia_utc():

    proximo = (
        inicio_dia_brasil()
        + timedelta(days=1)
    )

    return proximo.astimezone(
        timezone.utc
    ).isoformat()


# =========================================================
# ATIVIDADES
# =========================================================

ATIVIDADES = [
    "Peito / Ombro / Tríceps",
    "Dorsal / Bíceps",
    "Quadríceps / Glúteo / Panturrilha",
    "Perna completo",
    "Abdômen",
    "Peso corporal",
    "Corrida",
    "Futebol"
]


# =========================================================
# STORAGE - FOTO PRIVADA
# =========================================================

def enviar_foto(arquivo, participante_id):

    extensao = arquivo.name.lower().split(".")[-1]

    if extensao not in ["jpg", "jpeg", "png"]:

        st.error(
            "Formato de imagem não permitido."
        )

        return None

    nome = (
        f"{participante_id}/"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_"
        f"{secrets.token_hex(10)}."
        f"{extensao}"
    )

    url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"{BUCKET}/{nome}"
    )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": arquivo.type,
        "x-upsert": "false"
    }

    try:

        resposta = requests.post(
            url,
            headers=headers,
            data=arquivo.getvalue(),
            timeout=60
        )

        if resposta.status_code >= 400:

            st.error(
                f"Erro ao enviar foto: {resposta.text}"
            )

            return None

        return nome

    except Exception as erro:

        st.error(
            f"Erro no envio da foto: {erro}"
        )

        return None


def gerar_link_temporario(caminho):

    url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"sign/{BUCKET}/{caminho}"
    )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json={
                "expiresIn": 300
            },
            timeout=30
        )

        if resposta.status_code >= 400:

            return None

        dados = resposta.json()

        signed_url = dados.get("signedURL")

        if not signed_url:

            return None

        if signed_url.startswith("http"):

            return signed_url

        return (
            f"{SUPABASE_URL}/storage/v1"
            f"{signed_url}"
        )

    except Exception:

        return None


# =========================================================
# ATUALIZAR PARTICIPANTE
# =========================================================

def obter_participante(participante_id):

    resultado = supabase_get(
        "participantes",
        {
            "select": "*",
            "id": f"eq.{participante_id}",
            "limit": "1"
        }
    )

    if resultado:

        return resultado[0]

    return None


# =========================================================
# APROVAR E PAGAR BIO
# =========================================================

def adicionar_bio(participante_id, quantidade):

    pessoa = obter_participante(
        participante_id
    )

    if not pessoa:

        return False

    bio_atual = int(
        pessoa.get("bio", 0) or 0
    )

    resultado = supabase_update(
        "participantes",
        {
            "id": f"eq.{participante_id}"
        },
        {
            "bio": bio_atual + quantidade
        }
    )

    return resultado is not None


# =========================================================
# CABEÇALHO
# =========================================================

st.title("💪 BioCore")

st.write(
    "Treine, registre suas atividades e acumule BIO."
)


# =========================================================
# SAIR
# =========================================================

if st.session_state.participante or st.session_state.admin:

    if st.sidebar.button("Sair"):

        st.session_state.participante = None
        st.session_state.admin = False

        st.rerun()


# =========================================================
# ÁREA ADMINISTRADOR
# =========================================================

if st.session_state.admin:

    st.header("🔐 Área do administrador")

    st.success(
        "Administrador conectado."
    )


    # -----------------------------------------------------
    # PARTICIPANTES
    # -----------------------------------------------------

    st.subheader("👥 Participantes")

    participantes = supabase_get(
        "participantes",
        {
            "select": "*",
            "order": "created_at.desc"
        }
    )

    if not participantes:

        st.info(
            "Nenhum participante cadastrado."
        )

    else:

        for pessoa in participantes:

            st.markdown("---")

            st.write(
                f"**{pessoa.get('nome', '')}**"
            )

            st.write(
                f"📧 {pessoa.get('email', '')}"
            )

            st.write(
                f"💰 BIO: **{pessoa.get('bio', 0)}**"
            )

            wallet = pessoa.get(
                "wallet",
                ""
            )

            if wallet:

                st.write(
                    f"👛 Wallet: `{wallet}`"
                )

            else:

                st.write(
                    "👛 Wallet: não cadastrada"
                )


    # -----------------------------------------------------
    # TREINOS PENDENTES
    # -----------------------------------------------------

    st.subheader("🏃 Treinos pendentes")

    treinos = supabase_get(
        "treinos",
        {
            "select": "*",
            "status": "eq.Pendente",
            "bio_pago": "eq.false",
            "order": "created_at.asc"
        }
    )

    if not treinos:

        st.info(
            "Nenhum treino pendente."
        )

    else:

        for treino in treinos:

            participante_id = treino.get(
                "participante_id"
            )

            pessoa = obter_participante(
                participante_id
            )

            nome = (
                pessoa["nome"]
                if pessoa
                else "Participante"
            )

            st.markdown("---")

            st.write(
                f"**{nome}**"
            )

            st.write(
                f"🏋️ {treino.get('atividade', '')}"
            )

            st.caption(
                f"Registrado: {treino.get('created_at', '')}"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✅ Aprovar +10 BIO",
                    key=f"treino_ok_{treino['id']}"
                ):

                    atualizacao = supabase_update(
                        "treinos",
                        {
                            "id": f"eq.{treino['id']}",
                            "status": "eq.Pendente",
                            "bio_pago": "eq.false"
                        },
                        {
                            "status": "Aprovado",
                            "bio_pago": True
                        }
                    )

                    if atualizacao:

                        adicionar_bio(
                            participante_id,
                            10
                        )

                        st.success(
                            "Treino aprovado. +10 BIO."
                        )

                        st.rerun()

            with col2:

                if st.button(
                    "❌ Recusar",
                    key=f"treino_no_{treino['id']}"
                ):

                    supabase_update(
                        "treinos",
                        {
                            "id": f"eq.{treino['id']}"
                        },
                        {
                            "status": "Recusado"
                        }
                    )

                    st.rerun()


    # -----------------------------------------------------
    # COMPROVAÇÕES
    # -----------------------------------------------------

    st.subheader(
        "📸 Comprovações pendentes"
    )

    comprovacoes = supabase_get(
        "comprovacoes",
        {
            "select": "*",
            "status": "eq.Pendente",
            "bio_pago": "eq.false",
            "order": "created_at.asc"
        }
    )

    if not comprovacoes:

        st.info(
            "Nenhuma comprovação pendente."
        )

    else:

        for comprovacao in comprovacoes:

            participante_id = comprovacao.get(
                "participante_id"
            )

            pessoa = obter_participante(
                participante_id
            )

            nome = (
                pessoa["nome"]
                if pessoa
                else "Participante"
            )

            tipo = comprovacao.get(
                "tipo",
                "foto_semanal"
            )

            if tipo == "bioimpedancia":

                titulo
