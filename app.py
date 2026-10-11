import binascii
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
import streamlit as st


# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="💪",
    layout="centered",
)

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

BUCKET = "Comprovacoes"
FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")

# Temporário
ADMIN_PASSWORD = "1234"

ATIVIDADES = [
    "Peito / Ombro / Tríceps",
    "Dorsal / Bíceps",
    "Quadríceps / Glúteo / Panturrilha",
    "Perna completo",
    "Abdômen",
    "Peso corporal",
    "Corrida",
    "Futebol",
]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


# =========================================================
# SESSÃO
# =========================================================

def inicializar_sessao():
    if "participante" not in st.session_state:
        st.session_state.participante = None

    if "admin" not in st.session_state:
        st.session_state.admin = False


def sair():
    st.session_state.participante = None
    st.session_state.admin = False
    st.rerun()


inicializar_sessao()


# =========================================================
# SUPABASE
# =========================================================

def supabase_get(tabela, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    try:
        resposta = requests.get(
            url,
            headers=HEADERS,
            params=params or {},
            timeout=30,
        )

        if resposta.status_code >= 400:
            st.error(
                f"Erro ao consultar o banco: {resposta.text}"
            )
            return []

        return resposta.json()

    except Exception as erro:
        st.error(f"Erro de conexão: {erro}")
        return []


def supabase_insert(tabela, dados):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    headers = {
        **HEADERS,
        "Prefer": "return=representation",
    }

    try:
        resposta = requests.post(
            url,
            headers=headers,
            json=dados,
            timeout=30,
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
        st.error(f"Erro de conexão: {erro}")
        return None


def supabase_update(tabela, filtros, dados):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    headers = {
        **HEADERS,
        "Prefer": "return=representation",
    }

    try:
        resposta = requests.patch(
            url,
            headers=headers,
            params=filtros,
            json=dados,
            timeout=30,
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
        st.error(f"Erro de conexão: {erro}")
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
        200000,
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
            200000,
        )

        return secrets.compare_digest(
            binascii.hexlify(novo_hash).decode(),
            hash_hex,
        )

    except Exception:
        return False


# =========================================================
# DATA E HORA
# =========================================================

def agora_brasil():
    return datetime.now(FUSO_BRASIL)


def inicio_dia_brasil():
    return agora_brasil().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def inicio_dia_utc():
    return inicio_dia_brasil().astimezone(
        timezone.utc
    ).isoformat()


def inicio_proximo_dia_utc():
    proximo = inicio_dia_brasil() + timedelta(days=1)

    return proximo.astimezone(
        timezone.utc
    ).isoformat()


# =========================================================
# PARTICIPANTES
# =========================================================

def obter_participante(participante_id):
    resultado = supabase_get(
        "participantes",
        {
            "select": "*",
            "id": f"eq.{participante_id}",
            "limit": "1",
        },
    )

    return resultado[0] if resultado else None


def adicionar_bio(participante_id, quantidade):
    pessoa = obter_participante(participante_id)

    if not pessoa:
        return False

    bio_atual = int(
        pessoa.get("bio", 0) or 0
    )

    resultado = supabase_update(
        "participantes",
        {
            "id": f"eq.{participante_id}",
        },
        {
            "bio": bio_atual + quantidade,
        },
    )

    return resultado is not None


# =========================================================
# STORAGE
# =========================================================

def enviar_foto(arquivo, participante_id):
    extensao = arquivo.name.lower().split(".")[-1]

    if extensao not in ["jpg", "jpeg", "png"]:
        st.error("Formato de imagem não permitido.")
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
        "x-upsert": "false",
    }

    try:
        resposta = requests.post(
            url,
            headers=headers,
            data=arquivo.getvalue(),
            timeout=60,
        )

        if resposta.status_code >= 400:
            st.error(
                f"Erro ao enviar foto: {resposta.text}"
            )
            return None

        return nome

    except Exception as erro:
        st.error(f"Erro no envio da foto: {erro}")
        return None


def gerar_link_temporario(caminho):
    if not caminho:
        return None

    url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"sign/{BUCKET}/{caminho}"
    )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resposta = requests.post(
            url,
            headers=headers,
            json={"expiresIn": 300},
            timeout=30,
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
# CABEÇALHO E LOGOUT
# =========================================================

def mostrar_cabecalho():
    st.title("💪 BioCore")
    st.write(
        "Treine, registre suas atividades e acumule BIO."
    )


def mostrar_botao_sair():
    if (
        st.session_state.participante
        or st.session_state.admin
    ):
        if st.sidebar.button("Sair"):
            sair()


# =========================================================
# ADMIN — PARTICIPANTES
# =========================================================

def admin_participantes():
    st.subheader("👥 Participantes")

    participantes = supabase_get(
        "participantes",
        {
            "select": "*",
            "order": "created_at.desc",
        },
    )

    if not participantes:
        st.info("Nenhum participante cadastrado.")
        return

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

        wallet = pessoa.get("wallet", "")

        if wallet:
            st.write(
                f"👛 Wallet: `{wallet}`"
            )
        else:
            st.write(
                "👛 Wallet: não cadastrada"
            )


# =========================================================
# ADMIN — TREINOS
# =========================================================

def admin_treinos():
    st.subheader("🏃 Treinos pendentes")

    treinos = supabase_get(
        "treinos",
        {
            "select": "*",
            "status": "eq.Pendente",
            "bio_pago": "eq.false",
            "order": "created_at.asc",
        },
    )

    if not treinos:
        st.info("Nenhum treino pendente.")
        return

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

        st.write(f"**{nome}**")

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
                key=f"treino_ok_{treino['id']}",
            ):
                aprovado = supabase_update(
                    "treinos",
                    {
                        "id": f"eq.{treino['id']}",
                        "status": "eq.Pendente",
                        "bio_pago": "eq.false",
                    },
                    {
                        "status": "Aprovado",
                        "bio_pago": True,
                    },
                )

                if aprovado:
                    adicionar_bio(
                        participante_id,
                        10,
                    )

                    st.success(
                        "Treino aprovado. +10 BIO."
                    )

                    st.rerun()

        with col2:
            if st.button(
                "❌ Recusar",
                key=f"treino_no_{treino['id']}",
            ):
                supabase_update(
                    "treinos",
                    {
                        "id": f"eq.{treino['id']}",
                    },
                    {
                        "status": "Recusado",
                    },
                )

                st.rerun()


# =========================================================
# ADMIN — COMPROVAÇÕES
# =========================================================

def admin_comprovacoes():
    st.subheader("📸 Comprovações pendentes")

    comprovacoes = supabase_get(
        "comprovacoes",
        {
            "select": "*",
            "status": "eq.Pendente",
            "bio_pago": "eq.false",
            "order": "created_at.asc",
        },
    )

    if not comprovacoes:
        st.info("Nenhuma comprovação pendente.")
        return

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
            "foto_semanal",
        )

        if tipo == "bioimpedancia":
            titulo = "🧬 Bioimpedância"
            recompensa = 100
        else:
            titulo = "📸 Foto semanal"
            recompensa = 70

        st.markdown("---")

        st.write(f"**{nome}**")
        st.write(titulo)

        caminho = comprovacao.get(
            "arquivo_path"
        )

        link = gerar_link_temporario(caminho)

        if link:
            st.image(
                link,
                caption="Comprovação privada",
            )
        else:
            st.warning(
                "Não foi possível abrir esta foto."
            )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                f"✅ Aprovar +{recompensa} BIO",
                key=f"comp_ok_{comprovacao['id']}",
            ):
                aprovado = supabase_update(
                    "comprovacoes",
                    {
                        "id":
                        f"eq.{comprovacao['id']}",
                        "status":
                        "eq.Pendente",
                        "bio_pago":
                        "eq.false",
                    },
                    {
                        "status": "Aprovado",
                        "bio_pago": True,
                    },
                )

                if aprovado:
                    adicionar_bio(
                        participante_id,
                        recompensa,
                    )

                    st.success(
                        f"Aprovado. +{recompensa} BIO."
                    )

                    st.rerun()

        with col2:
            if st.button(
                "❌ Recusar",
                key=f"comp_no_{comprovacao['id']}",
            ):
                supabase_update(
                    "comprovacoes",
                    {
                        "id":
                        f"eq.{comprovacao['id']}",
                    },
                    {
                        "status": "Recusado",
                    },
                )

                st.rerun()


# =========================================================
# ADMIN — CASHBACK
# =========================================================

def admin_cashback():
    st.subheader("💵 Solicitações de cashback")

    solicitacoes = supabase_get(
        "participantes",
        {
            "select": "*",
            "cashback_solicitado": "eq.true",
        },
    )

    if not solicitacoes:
        st.info(
            "Nenhuma solicitação de cashback."
        )
        return

    for pessoa in solicitacoes:
        st.markdown("---")

        st.write(
            f"**{pessoa.get('nome', '')}**"
        )

        st.write(
            f"BIO: **{pessoa.get('bio', 0)}**"
        )

        wallet = pessoa.get(
            "wallet",
            "",
        )

        st.write(
            f"👛 Wallet: `{wallet}`"
        )

        if st.button(
            "💵 Marcar como pago",
            key=f"cash_{pessoa['id']}",
        ):
            supabase_update(
                "participantes",
                {
                    "id":
                    f"eq.{pessoa['id']}",
                },
                {
                    "cashback_solicitado":
                    False,
                    "cashback_pago":
                    True,
                },
            )

            st.success(
                "Pagamento marcado."
            )

            st.rerun()


# =========================================================
# ÁREA ADMINISTRADOR
# =========================================================

def mostrar_admin():
    st.header("🔐 Área do administrador")

    st.success(
        "Administrador conectado."
    )

    admin_participantes()
    admin_treinos()
    admin_comprovacoes()
    admin_cashback()

    st.sidebar.success(
        "👑 Administrador"
    )


# =========================================================
# LOGIN DO ADMINISTRADOR
# =========================================================

def mostrar_login_admin():
    with st.expander(
        "🔐 Área do administrador"
    ):
        senha_admin = st.text_input(
            "Senha do administrador",
            type="password",
        )

        if st.button(
            "Entrar como administrador"
        ):
            if senha_admin == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.rerun()
            else:
                st.error(
                    "Senha incorreta."
                )


# =========================================================
# ORIENTAÇÕES
# =========================================================

def mostrar_orientacao():
    with st.expander(
        "🩺 Orientação antes de treinar"
    ):
        st.write(
            """
            Antes de iniciar ou aumentar a intensidade
            dos exercícios, recomendamos verificar sua
            aptidão para atividade física com um médico
            ou profissional de saúde habilitado quando
            necessário.

            Respeite seus limites.

            Se sentir dor, tontura, falta de ar anormal,
            mal-estar ou outro sintoma durante a atividade,
            interrompa o exercício e procure atendimento
            profissional.

            O BioCore não substitui avaliação, diagnóstico
            ou tratamento médico.
            """
        )


def mostrar_termos():
    with st.expander(
        "📋 Termos e privacidade"
    ):
        st.write(
            """
            As fotos enviadas ao BioCore são utilizadas
            exclusivamente para comprovação das atividades.

            As fotos não serão divulgadas publicamente
            pelo BioCore sem uma autorização específica.

            Os dados são utilizados para administrar a
            conta, registrar atividades, analisar
            comprovações e administrar as recompensas.
            """
        )


# =========================================================
# PARTICIPANTE — TREINO
# =========================================================

def registrar_treino(participante_id):
    st.subheader("🏋️ Registrar atividade")

    st.caption(
        "Limite: 1 atividade registrada por dia."
    )

    inicio = inicio_dia_utc()
    fim = inicio_proximo_dia_utc()

    treinos_hoje = supabase_get(
        "treinos",
        {
            "select": "id",
            "participante_id":
            f"eq.{participante_id}",
            "created_at":
            f"gte.{inicio}",
            "and":
            f"(created_at.lt.{fim})",
        },
    )

    if treinos_hoje:
        st.info(
            "Você já registrou uma atividade hoje."
        )
        return

    atividade = st.selectbox(
        "Escolha a atividade",
        ATIVIDADES,
    )

    if st.button(
        "Registrar treino"
    ):
        resultado = supabase_insert(
            "treinos",
            {
                "participante_id":
                participante_id,
                "atividade":
                atividade,
                "status":
                "Pendente",
                "bio_pago":
                False,
            },
        )

        if resultado:
            st.success(
                "Treino registrado. Aguarde a aprovação."
            )
            st.rerun()


# =========================================================
# PARTICIPANTE — FOTO SEMANAL
# =========================================================

def enviar_foto_semanal(participante_id):
    st.subheader("📸 Foto semanal")

    st.write(
        "Recompensa: 70 BIO após aprovação."
    )

    sete_dias = (
        datetime.now(timezone.utc)
        - timedelta(days=7)
    ).isoformat()

    fotos = supabase_get(
        "comprovacoes",
        {
            "select": "*",
            "participante_id":
            f"eq.{participante_id}",
            "tipo":
            "eq.foto_semanal",
            "created_at":
            f"gte.{sete_dias}",
            "order":
            "created_at.desc",
        },
    )

    if fotos:
        ultima = fotos[0]

        status = ultima.get(
            "status",
            "Pendente",
        )

        if status == "Pendente":
            st.warning(
                "Sua foto está aguardando aprovação."
            )

        elif status == "Aprovado":
            st.success(
                "Foto aprovada. +70 BIO."
            )

        else:
            st.warning(
                "A última foto foi recusada."
            )

        return

    foto = st.file_uploader(
        "Escolha a foto",
        type=["jpg", "jpeg", "png"],
        key="foto_semanal",
    )

    if foto and st.button(
        "Enviar foto semanal"
    ):
        caminho = enviar_foto(
            foto,
            participante_id,
        )

        if caminho:
            resultado = supabase_insert(
                "comprovacoes",
                {
                    "participante_id":
                    participante_id,
                    "nome_arquivo":
                    foto.name,
                    "arquivo_path":
                    caminho,
                    "tipo":
                    "foto_semanal",
                    "status":
                    "Pendente",
                    "bio_pago":
                    False,
                },
            )

            if resultado:
                st.success(
                    "Foto enviada para análise."
                )
                st.rerun()


# =========================================================
# PARTICIPANTE — BIOIMPEDÂNCIA
# =========================================================

def enviar_bioimpedancia(participante_id):
    st.subheader("🧬 Bioimpedância")

    st.write(
        "Recompensa: 100 BIO após aprovação."
    )

    bioimpedancias = supabase_get(
        "comprovacoes",
        {
            "select": "*",
            "participante_id":
            f"eq.{participante_id}",
            "tipo":
            "eq.bioimpedancia",
            "order":
            "created_at.desc",
            "limit":
            "1",
        },
    )

    if bioimpedancias:
        ultima = bioimpedancias[0]

        status = ultima.get(
            "status",
            "Pendente",
        )

        if status == "Pendente":
            st.info(
                "Sua bioimpedância está aguardando aprovação."
            )

        elif status == "Aprovado":
            st.success(
                "Bioimpedância aprovada. +100 BIO."
            )

        else:
            st.warning(
                "A última bioimpedância foi recusada."
            )

        return

    bioimp = st.file_uploader(
        "Enviar comprovante",
        type=["jpg", "jpeg", "png"],
        key="bioimpedancia",
    )

    if bioimp and st.button(
        "Enviar bioimpedância"
    ):
        caminho = enviar_foto(
            bioimp,
            participante_id,
        )

        if caminho:
            resultado = supabase_insert(
                "comprovacoes",
                {
                    "participante_id":
                    participante_id,
                    "nome_arquivo":
                    bioimp.name,
                    "arquivo_path":
                    caminho,
                    "tipo":
                    "bioimpedancia",
                    "status":
                    "Pendente",
                    "bio_pago":
                    False,
                },
            )

            if resultado:
                st.success(
        "Comprovante enviado para análise."
    )
                st.rerun()
                
# =========================================================
# PARTICIPANTE — WALLET
# =========================================================

def mostrar_wallet(participante):
    st.subheader("👛 Minha Trust Wallet")

    participante_id = participante["id"]

    wallet_atual = (
        participante.get("wallet", "")
        or ""
    )

    wallet = st.text_input(
        "Endereço da carteira",
        value=wallet_atual,
        placeholder=(
            "Cole aqui o endereço da sua carteira"
        ),
    )

    if st.button(
        "Salvar carteira"
    ):
        supabase_update(
            "participantes",
            {
                "id":
                f"eq.{participante_id}",
            },
            {
                "wallet":
                wallet.strip(),
            },
        )

        st.success(
            "Carteira salva."
        )

        st.rerun()

# =========================================================
# PARTICIPANTE — CHAVE PIX
# =========================================================

def mostrar_chave_pix(participante):
    st.subheader("💳 Minha chave Pix")

    participante_id = participante["id"]

    chave_pix_atual = (
        participante.get("chave_pix", "")
        or ""
    )

    chave_pix = st.text_input(
        "Chave Pix",
        value=chave_pix_atual,
        placeholder="Digite sua chave Pix",
        key=f"chave_pix_{participante_id}",
    )

    if st.button(
        "Salvar chave Pix",
        key=f"salvar_pix_{participante_id}",
    ):
        chave_pix = chave_pix.strip()

        if not chave_pix:
            st.error("Digite sua chave Pix.")
            return

        resultado = supabase_update(
            "participantes",
            {
                "id":
                f"eq.{participante_id}",
            },
            {
                "chave_pix":
                chave_pix,
            },
        )

        if resultado is not None:
            st.success("Chave Pix salva com sucesso.")
            st.rerun()
            
# =========================================================
# PARTICIPANTE — CASHBACK
# =========================================================

def mostrar_cashback(participante, bio):
    st.subheader("💶 MEU CASHBACK")

    # Limite do ciclo
    bio_meta = 5000
    cashback_maximo = 50.00

    # Garante que o BIO não ultrapasse a meta para o cálculo visual
    bio_progresso = min(max(bio, 0), bio_meta)

    # Calcula o cashback proporcional ao BIO acumulado
    cashback = (bio_progresso / bio_meta) * cashback_maximo

    # Percentual da barra
    progresso = bio_progresso / bio_meta

    st.metric(
        "Cashback acumulado",
        f"R$ {cashback:.2f}"
    )

    st.progress(progresso)

    st.write(
        f"**{bio_progresso:,.0f} / {bio_meta:,.0f} BIO**"
        .replace(",", ".")
    )

    st.write(
        f"**R$ {cashback:.2f} / R$ {cashback_maximo:.2f}**"
    )

    if bio >= bio_meta:
        st.success(
            "🎉 Você atingiu 5.000 BIO e pode solicitar até R$50 de cashback."
        )

        if participante.get(
            "cashback_solicitado",
            False,
        ):
            st.info(
                "Sua solicitação está aguardando análise."
            )

        else:
            if st.button(
                "💶 Solicitar cashback de até R$50"
            ):
                supabase_update(
                    "participantes",
                    {
                        "id":
                        f"eq.{participante['id']}",
                    },
                    {
                        "cashback_solicitado":
                        True,
                        "cashback_pago":
                        False,
                    },
                )

                st.success(
                    "Solicitação enviada ao administrador."
                )

                st.rerun()

    else:
        faltam = bio_meta - bio

        st.info(
            f"Faltam {faltam:,} BIO para atingir R$50 de cashback."
            .replace(",", ".")
        )


# =========================================================
# PARTICIPANTE — LINKS
# =========================================================

def mostrar_links():
    st.subheader("🔗 Acessos")

    st.link_button(
    "🛒 Mercado Livre",
    "https://www.mercadolivre.com.br/social/sama6231844"
)


    

    st.caption(
        "Link de afiliado do Mercado Livre."
    )

    st.link_button(
        "🏪 CoreStryke",
        "https://corestryke.com/",
    )

    st.caption(
        "CoreStryke é a loja do BioCore."
    )

    st.link_button(
        "👛 Trust Wallet",
        "https://trustwallet.com/",
    )

    st.caption(
        "O BioCore não possui parceria oficial com a Trust Wallet."
    )


# =========================================================
# ÁREA DO PARTICIPANTE
# =========================================================

def mostrar_participante():
    participante_id = (
        st.session_state.participante["id"]
    )

    participante = obter_participante(
        participante_id
    )

    if not participante:
        st.session_state.participante = None

        st.error(
            "Não foi possível carregar sua conta."
        )

        st.stop()

    st.session_state.participante = participante

    st.header(
        f"Olá, {participante['nome']}! 👋"
    )

    # JOGO DE SUPINO BIOCORE
    mostrar_jogo_supino()

    bio = int(
        participante.get("bio", 0) or 0
    )

    st.metric(
        "💰 Meu saldo BIO",
        f"{bio:,}".replace(",", "."),
    )

    mostrar_orientacao()
    mostrar_termos()

    registrar_treino(
        participante_id
    )

    enviar_foto_semanal(
        participante_id
    )

    enviar_bioimpedancia(
        participante_id
    )

    mostrar_wallet(
        participante
    )

    mostrar_chave_pix(
        participante
    )

    mostrar_cashback(
        participante,
        bio
    )

    mostrar_links()


# =========================================================
# LOGIN DO PARTICIPANTE
# =========================================================

def login_participante():
    email = st.text_input(
        "E-mail",
        key="login_email",
    )

    senha = st.text_input(
        "Senha",
        type="password",
        key="login_senha",
    )

    if st.button(
        "Entrar",
        key="entrar_participante",
    ):
        usuarios = supabase_get(
            "participantes",
            {
                "select": "*",
                "email":
                f"eq.{email.strip().lower()}",
                "limit":
                "1",
            },
        )

        if not usuarios:
            st.error(
                "E-mail ou senha incorretos."
            )
            return

        usuario = usuarios[0]

        if verificar_senha(
            senha,
            usuario["senha_hash"],
        ):
            st.session_state.participante = usuario
            st.rerun()
        else:
            st.error(
                "E-mail ou senha incorretos."
            )


# =========================================================
# CADASTRO
# =========================================================

def cadastro_participante():
    st.subheader("Criar cadastro")

    nome = st.text_input(
        "Nome",
        key="cad_nome",
    )

    email = st.text_input(
        "E-mail",
        key="cad_email",
    )

    senha = st.text_input(
        "Senha",
        type="password",
        key="cad_senha",
    )

    confirmar_senha = st.text_input(
        "Confirmar senha",
        type="password",
        key="cad_confirmar",
    )

    st.markdown(
        "### 🩺 Antes de participar"
    )

    st.write(
        """
        Antes de iniciar ou aumentar a intensidade dos
        exercícios, recomendamos verificar sua aptidão
        para atividade física com um médico ou profissional
        de saúde habilitado quando necessário.

        Respeite seus limites.

        Se sentir dor, tontura, falta de ar anormal,
        mal-estar ou outro sintoma durante a atividade,
        interrompa o exercício e procure atendimento.
        """
    )

    st.markdown(
        "### 🔒 Privacidade"
    )

    st.write(
        """
        As fotos enviadas ao BioCore serão utilizadas
        para comprovação das atividades.

        As fotos não serão divulgadas publicamente
        pelo BioCore sem autorização específica.
        """
    )

    aceita_termos = st.checkbox(
        "Li e concordo com os Termos de Uso e a Política de Privacidade."
    )

    ciente_atividade = st.checkbox(
        "Estou ciente da orientação sobre atividade física e procurarei orientação profissional quando necessário."
    )

    if st.button(
        "Criar cadastro",
        key="criar_conta",
    ):
        criar_conta(
            nome,
            email,
            senha,
            confirmar_senha,
            aceita_termos,
            ciente_atividade,
        )


def criar_conta(
    nome,
    email,
    senha,
    confirmar_senha,
    aceita_termos,
    ciente_atividade,
):
    if not nome.strip():
        st.error("Digite seu nome.")
        return

    if not email.strip():
        st.error("Digite seu e-mail.")
        return

    if len(senha) < 6:
        st.error(
            "A senha precisa ter pelo menos 6 caracteres."
        )
        return

    if senha != confirmar_senha:
        st.error(
            "As senhas não são iguais."
        )
        return

    if not aceita_termos:
        st.error(
            "Você precisa aceitar os Termos e a Política de Privacidade."
        )
        return

    if not ciente_atividade:
        st.error(
            "Confirme que está ciente da orientação sobre atividade física."
        )
        return

    email_normalizado = (
        email.strip().lower()
    )

    existente = supabase_get(
        "participantes",
        {
            "select": "id",
            "email":
            f"eq.{email_normalizado}",
            "limit":
            "1",
        },
    )

    if existente:
        st.error(
            "Esse e-mail já está cadastrado."
        )
        return

    senha_hash = criar_hash_senha(
        senha
    )

    novo = supabase_insert(
        "participantes",
        {
            "nome":
            nome.strip(),
            "email":
            email_normalizado,
            "senha_hash":
            senha_hash,
            "wallet":
            "",
            "bio":
            0,
            "cashback_solicitado":
            False,
            "cashback_pago":
            False,
        },
    )

    if novo:
        st.success(
            "Cadastro criado com sucesso! Agora entre na sua conta."
        )


# =========================================================
# TELA DE LOGIN / CADASTRO
# =========================================================

def mostrar_login_cadastro():
    st.header("Bem-vindo ao BioCore")

    aba_login, aba_cadastro = st.tabs(
        ["Entrar", "Criar cadastro"]
    )

    with aba_login:
        login_participante()

    with aba_cadastro:
        cadastro_participante()

        
def mostrar_jogo_supino():
    st.components.v1.html(
        """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 8px;
    background: #17151f;
    color: white;
    font-family: Arial, sans-serif;
    text-align: center;
}

.game {
    max-width: 520px;
    margin: auto;
    padding: 12px;
    border-radius: 18px;
    background: #242131;
}

h2 {
    margin: 4px 0 12px;
    color: #f0abfc;
    font-size: 22px;
}

.gym {
    position: relative;
    height: 280px;
    overflow: hidden;
    border-radius: 14px;
    background:
        radial-gradient(ellipse at 50% 20%, #49415e, transparent 70%),
        linear-gradient(#302b40, #17151f);
}

.floor {
    position: absolute;
    bottom: 0;
    width: 100%;
    height: 38px;
    background: #292635;
    border-top: 3px solid #514a60;
}

/* Banco */
.bench {
    position: absolute;
    left: 15%;
    bottom: 76px;
    width: 61%;
    height: 17px;
    border-radius: 7px;
    background: linear-gradient(#b6bbc6, #626979);
    z-index: 2;
}

.bench-support {
    position: absolute;
    left: 42%;
    bottom: 39px;
    height: 41px;
    width: 10px;
    background: #717784;
    z-index: 1;
}

.bench-foot {
    position: absolute;
    left: 31%;
    bottom: 35px;
    width: 33%;
    height: 7px;
    background: #a1a1aa;
    border-radius: 5px;
    z-index: 2;
}

/* Cabeça e rosto */
.head {
    position: absolute;
    left: 15%;
    top: 143px;
    width: 34px;
    height: 37px;
    border-radius: 45% 45% 42% 42%;
    background: #d9a17e;
    z-index: 5;
}

.hair {
    position: absolute;
    left: 14.5%;
    top: 140px;
    width: 35px;
    height: 15px;
    border-radius: 70% 60% 20% 15%;
    background: #30251f;
    z-index: 6;
}

.eye {
    position: absolute;
    left: 20%;
    top: 157px;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #30251f;
    z-index: 7;
}

.neck {
    position: absolute;
    left: 21%;
    top: 166px;
    width: 17px;
    height: 21px;
    border-radius: 5px;
    background: #c58e6d;
    z-index: 3;
}

/* Tronco atlético */
.torso {
    position: absolute;
    left: 23%;
    top: 166px;
    width: 34%;
    height: 34px;
    border-radius: 14px 19px 12px 12px;
    background: linear-gradient(180deg, #a855f7, #6b21a8);
    transform: rotate(-2deg);
    z-index: 4;
}

.shirt-seam {
    position: absolute;
    left: 39%;
    top: 168px;
    height: 28px;
    width: 2px;
    background: #d8b4fe;
    z-index: 5;
}

/* Cintura e calção */
.hip {
    position: absolute;
    left: 53%;
    top: 172px;
    width: 20%;
    height: 29px;
    border-radius: 9px;
    background: #4c1d95;
    z-index: 4;
}

/* Pernas */
.leg {
    position: absolute;
    top: 188px;
    width: 17px;
    height: 53px;
    border-radius: 9px;
    background: #334155;
    transform-origin: top center;
    z-index: 3;
}

.leg-left {
    left: 61%;
    transform: rotate(35deg);
}

.leg-right {
    left: 69%;
    transform: rotate(43deg);
}

.shoe {
    position: absolute;
    width: 27px;
    height: 12px;
    border-radius: 8px 12px 5px 5px;
    background: #e879f9;
    z-index: 4;
}

.shoe-left {
    left: 73%;
    top: 231px;
    transform: rotate(27deg);
}

.shoe-right {
    left: 81%;
    top: 239px;
    transform: rotate(34deg);
}

/* Braços: movimento acompanha a barra */
.arm {
    position: absolute;
    top: 83px;
    width: 13px;
    height: 78px;
    border-radius: 10px;
    background: #d9a17e;
    transform-origin: 50% 90%;
    transition: transform .3s ease;
    z-index: 6;
}

.arm-left {
    left: 34%;
    transform: rotate(-9deg);
}

.arm-right {
    left: 49%;
    transform: rotate(9deg);
}

.hand {
    position: absolute;
    top: 78px;
    width: 17px;
    height: 15px;
    border-radius: 7px;
    background: #d9a17e;
    transition: top .3s ease;
    z-index: 7;
}

.hand-left { left: 32%; }
.hand-right { left: 48%; }

/* Barra e anilhas */
.bar {
    position: absolute;
    left: 7%;
    top: 76px;
    width: 86%;
    height: 9px;
    border-radius: 5px;
    background: linear-gradient(#fff, #9ca3af);
    box-shadow: 0 3px 5px #0007;
    transition: top .3s ease;
    z-index: 8;
}

.plate {
    position: absolute;
    top: -14px;
    width: 18px;
    height: 37px;
    border: 3px solid #a21caf;
    border-radius: 5px;
    background: linear-gradient(90deg, #e879f9, #86198f);
}

.plate-left { left: 5%; }
.plate-right { right: 5%; }

.stats {
    display: flex;
    justify-content: space-around;
    gap: 7px;
    margin: 13px 0;
}

.stat {
    flex: 1;
    padding: 10px 3px;
    border-radius: 10px;
    background: #302b40;
    font-size: 11px;
}

.number {
    display: block;
    margin-top: 5px;
    color: #f0abfc;
    font-size: 23px;
    font-weight: bold;
}

.message {
    min-height: 42px;
    padding: 10px 2px;
    color: #e9d5ff;
    font-size: 14px;
}

button {
    width: 47%;
    margin: 4px 1%;
    padding: 14px 3px;
    border: 0;
    border-radius: 12px;
    background: #a21caf;
    color: white;
    font-size: 14px;
    font-weight: bold;
    touch-action: manipulation;
}

button:disabled { opacity: .35; }

.start {
    width: 98%;
    background: #7e22ce;
}

.reward {
    margin-top: 10px;
    padding: 11px;
    border-radius: 10px;
    background: #302b40;
    color: #e9d5ff;
    font-size: 13px;
}

.hint {
    color: #c4b5fd;
    font-size: 11px;
}
</style>
</head>

<body>
<div class="game">
    <h2>🏋️ BIOCORE SUPINO</h2>

    <div class="gym">
        <div class="floor"></div>
        <div class="bench-support"></div>
        <div class="bench-foot"></div>
        <div class="bench"></div>

        <div class="leg leg-left"></div>
        <div class="leg leg-right"></div>
        <div class="shoe shoe-left"></div>
        <div class="shoe shoe-right"></div>

        <div class="hip"></div>
        <div class="torso"></div>
        <div class="shirt-seam"></div>
        <div class="neck"></div>
        <div class="head"></div>
        <div class="hair"></div>
        <div class="eye"></div>

        <div class="arm arm-left" id="armLeft"></div>
        <div class="arm arm-right" id="armRight"></div>
        <div class="hand hand-left" id="handLeft"></div>
        <div class="hand hand-right" id="handRight"></div>

        <div class="bar" id="bar">
            <span class="plate plate-left"></span>
            <span class="plate plate-right"></span>
        </div>
    </div>

    <div class="stats">
        <div class="stat">
            SÉRIE
            <span class="number" id="series">0/4</span>
        </div>
        <div class="stat">
            REPETIÇÕES
            <span class="number" id="reps">0/10</span>
        </div>
        <div class="stat">
            TOTAL
            <span class="number" id="total">0</span>
        </div>
    </div>

    <div class="message" id="msg">
        Toque em COMEÇAR para iniciar!
    </div>

    <button class="start" id="start" onclick="startGame()">
        COMEÇAR
    </button>

    <div>
        <button id="down" onclick="lower()" disabled>
            ⬇ DESCER
        </button>
        <button id="up" onclick="raise()" disabled>
            ⬆ SUBIR
        </button>
    </div>

    <div class="reward">
        Recompensa prevista: <strong>0,005 BIO</strong> por repetição.
        <br>
        40 repetições = <strong>0,2 BIO previsto</strong>.
    </div>

    <p class="hint">
        Desça e depois suba a barra para validar cada repetição.
    </p>
</div>

<script>
let started = false;
let lowered = false;
let reps = 0;
let series = 0;
let total = 0;

const bar = document.getElementById("bar");
const msg = document.getElementById("msg");
const start = document.getElementById("start");
const down = document.getElementById("down");
const up = document.getElementById("up");
const armLeft = document.getElementById("armLeft");
const armRight = document.getElementById("armRight");
const handLeft = document.getElementById("handLeft");
const handRight = document.getElementById("handRight");

function updateStats() {
    document.getElementById("series").textContent = series + "/4";
    document.getElementById("reps").textContent = reps + "/10";
    document.getElementById("total").textContent = total;
}

function startGame() {
    if (series >= 4 || started) return;

    started = true;
    lowered = false;
    start.disabled = true;
    down.disabled = false;
    up.disabled = false;

    bar.style.top = "76px";
    armLeft.style.transform = "rotate(-9deg)";
    armRight.style.transform = "rotate(9deg)";
    handLeft.style.top = "78px";
    handRight.style.top = "78px";

    msg.textContent = "Desça a barra até o peito.";
}

function lower() {
    if (!started || lowered || series >= 4) return;

    lowered = true;
    bar.style.top = "133px";
    armLeft.style.transform = "rotate(-30deg)";
    armRight.style.transform = "rotate(30deg)";
    handLeft.style.top = "135px";
    handRight.style.top = "135px";

    msg.textContent = "Agora empurre a barra para cima!";
}

function raise() {
    if (!started || !lowered || series >= 4) return;

    lowered = false;
    bar.style.top = "76px";
    armLeft.style.transform = "rotate(-9deg)";
    armRight.style.transform = "rotate(9deg)";
    handLeft.style.top = "78px";
    handRight.style.top = "78px";

    reps++;
    total++;
    updateStats();

    if (reps >= 10) {
        reps = 0;
        series++;
        updateStats();

        if (series >= 4) {
            started = false;
            down.disabled = true;
            up.disabled = true;
            start.disabled = true;
            start.textContent = "DESAFIO CONCLUÍDO";
            msg.textContent =
                "Desafio concluído! " + total +
                " repetições. BIO previsto: 0,2.";
        } else {
            started = false;
            down.disabled = true;
            up.disabled = true;
            start.disabled = false;
            start.textContent = "COMEÇAR SÉRIE " + (series + 1);
            msg.textContent =
                "Série concluída! Descanse e continue.";
        }
    } else {
        msg.textContent =
            "+0,005 BIO previsto! Faça a próxima descida.";
    }
}
</script>
</body>
</html>
        """,
        height=680,
        scrolling=False,
)



def mostrar_jogo_agachamento():
    st.components.v1.html(
        """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          * { box-sizing: border-box; }
          body {
            margin: 0;
            padding: 10px;
            background: #11121b;
            color: white;
            font-family: Arial, sans-serif;
          }
          .game {
            max-width: 760px;
            margin: auto;
            padding: 12px;
            border-radius: 18px;
            background: linear-gradient(160deg,#29253d,#11121b);
            border: 1px solid #49405f;
          }
          h2 { text-align:center; margin:8px 0; font-size:20px; }
          .sub { text-align:center; color:#d0c9e6; font-size:13px; }
          #scene {
            width:100%;
            height:360px;
            overflow:hidden;
            border-radius:14px;
            background:#171b2b;
            margin-top:10px;
          }
          #scene canvas { display:block; }
          .stats {
            display:grid;
            grid-template-columns:repeat(3,1fr);
            gap:7px;
            margin-top:10px;
          }
          .stat {
            text-align:center;
            background:#302e46;
            padding:10px 3px;
            border-radius:10px;
            font-size:11px;
          }
          .stat strong {
            display:block;
            color:#e1b5ff;
            font-size:18px;
            margin-top:5px;
          }
          .progress {
            height:9px;
            background:#454258;
            border-radius:10px;
            overflow:hidden;
            margin:12px 0;
          }
          #fill {
            width:0%;
            height:100%;
            background:linear-gradient(90deg,#a855f7,#f0abfc);
          }
          .controls {
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:10px;
          }
          button {
            padding:15px 5px;
            border:0;
            border-radius:12px;
            color:white;
            background:#8138cb;
            font-size:15px;
            font-weight:bold;
            touch-action:manipulation;
          }
          #rise { background:#16766b; }
          #reset {
            width:100%;
            margin-top:8px;
            background:#414154;
          }
          #message {
            text-align:center;
            color:#f0d9ff;
            margin-top:10px;
            font-weight:bold;
          }
          .notice {
            font-size:11px;
            color:#bbb8cf;
            text-align:center;
            margin-top:10px;
            line-height:1.5;
          }
        </style>
        </head>
        <body>
        <div class="game">
          <h2>🏋️ BIOCORE — AGACHAMENTO 3D</h2>
          <div class="sub">Agache com a barra e volte à posição inicial</div>
          <div id="scene"></div>

          <div class="stats">
            <div class="stat">SÉRIE
              <strong id="series">1 / 4</strong>
            </div>
            <div class="stat">REPETIÇÕES
              <strong id="reps">0 / 40</strong>
            </div>
            <div class="stat">BIO ESTIMADO
              <strong id="bio">0.000</strong>
            </div>
          </div>

          <div class="progress"><div id="fill"></div></div>

          <div class="controls">
            <button id="down">⬇ AGACHAR</button>
            <button id="rise">⬆ SUBIR</button>
          </div>
          <button id="reset">↻ RECOMEÇAR</button>
          <div id="message">Pronto para começar!</div>

          <div class="notice">
            Meta: 4 séries de 10 repetições.<br>
            Recompensa demonstrativa: 0,005 BIO por repetição.<br>
            Este protótipo não deposita BIO na carteira.
          </div>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script>
        (() => {
          const holder = document.getElementById('scene');

          if (!window.THREE) {
            holder.innerHTML =
              '<p style="padding:20px;text-align:center">' +
              'Não foi possível carregar o 3D. Verifique a internet.' +
              '</p>';
            return;
          }

          const scene = new THREE.Scene();
          scene.background = new THREE.Color(0x171b2b);

          const camera = new THREE.PerspectiveCamera(
            42, holder.clientWidth / holder.clientHeight, 0.1, 100
          );
          camera.position.set(0.25, 2.6, 8.8);
          camera.lookAt(0, 1.35, 0);

          const renderer = new THREE.WebGLRenderer({antialias:true});
          renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
          renderer.setSize(holder.clientWidth, holder.clientHeight);
          renderer.outputEncoding = THREE.sRGBEncoding;
          holder.appendChild(renderer.domElement);

          scene.add(new THREE.HemisphereLight(0xdde5ff, 0x302039, 2));

          const light = new THREE.DirectionalLight(0xffffff, 2.4);
          light.position.set(-3, 7, 5);
          scene.add(light);

          const purpleLight = new THREE.PointLight(0xb34cff, 2);
          purpleLight.position.set(3, 3, 2);
          scene.add(purpleLight);

          function mat(color, metalness=0, roughness=0.55) {
            return new THREE.MeshStandardMaterial({
              color:color,
              metalness:metalness,
              roughness:roughness
            });
          }

          const skin = mat(0xc98d69);
          const shirt = mat(0x8537d0);
          const shorts = mat(0x25273b);
          const shoes = mat(0xe4e7f4);
          const steel = mat(0xc3cad6,0.85,0.25);
          const plateMat = mat(0x252735,0.45,0.3);
        </script>
        </body>
        </html>
        """,
        height=650,
        scrolling=False,
    )

          function sphere(parent, x, y, z, sx, sy, sz, material) {
            const mesh = new THREE.Mesh(
              new THREE.SphereGeometry(1, 24, 16),
              material
            );
            mesh.position.set(x, y, z);
            mesh.scale.set(sx, sy, sz);
            parent.add(mesh);
            return mesh;
          }

          function cylinder(parent, x, y, z, radius, length, material) {
            const mesh = new THREE.Mesh(
              new THREE.CylinderGeometry(radius, radius, length, 24),
              material
            );
            mesh.position.set(x, y, z);
            parent.add(mesh);
            return mesh;
          }

          function limb(parent, start, end, radius, material) {
            const a = new THREE.Vector3(...start);
            const b = new THREE.Vector3(...end);
            const direction = new THREE.Vector3().subVectors(b, a);

            const mesh = new THREE.Mesh(
              new THREE.CylinderGeometry(
                radius * 0.8, radius, direction.length(), 20
              ),
              material
            );

            mesh.position.copy(a).add(b).multiplyScalar(0.5);
            mesh.quaternion.setFromUnitVectors(
              new THREE.Vector3(0, 1, 0),
              direction.normalize()
            );
            parent.add(mesh);
            return mesh;
          }

          // Personagem
          const athlete = new THREE.Group();
          scene.add(athlete);

          // Tronco, peito, pescoço e cabeça
          sphere(athlete, 0, 1.78, 0, 0.44, 0.55, 0.28, shirt);
          sphere(athlete, 0, 1.99, 0.13, 0.38, 0.25, 0.21, shirt);
          cylinder(athlete, 0, 2.30, 0, 0.11, 0.15, skin);
          sphere(athlete, 0, 2.53, 0, 0.23, 0.26, 0.22, skin);

          // Olhos
          sphere(athlete, -0.075, 2.56, 0.202, 0.025, 0.025, 0.012, plateMat);
          sphere(athlete,  0.075, 2.56, 0.202, 0.025, 0.025, 0.012, plateMat);

          // Quadril e shorts
          sphere(athlete, 0, 1.22, 0, 0.38, 0.23, 0.24, shorts);

          // Pernas com articulação nos joelhos
          const leftLeg = new THREE.Group();
          leftLeg.position.set(-0.21, 1.15, 0);
          athlete.add(leftLeg);

          limb(leftLeg, [0,0,0], [0,-0.47,0], 0.145, skin);
          sphere(leftLeg, 0,-0.47,0, 0.14,0.14,0.14, skin);

          const leftCalf = new THREE.Group();
          leftCalf.position.set(0,-0.47,0);
          leftLeg.add(leftCalf);

          limb(leftCalf, [0,0,0], [0,-0.47,0], 0.10, skin);
          sphere(leftCalf, 0,-0.46,0.02, 0.105,0.12,0.11, skin);
          sphere(leftCalf, 0,-0.51,0.10, 0.15,0.085,0.23, shoes);

          const rightLeg = new THREE.Group();
          rightLeg.position.set(0.21, 1.15, 0);
          athlete.add(rightLeg);

          limb(rightLeg, [0,0,0], [0,-0.47,0], 0.145, skin);
          sphere(rightLeg, 0,-0.47,0, 0.14,0.14,0.14, skin);

          const rightCalf = new THREE.Group();
          rightCalf.position.set(0,-0.47,0);
          rightLeg.add(rightCalf);

          limb(rightCalf, [0,0,0], [0,-0.47,0], 0.10, skin);
          sphere(rightCalf, 0,-0.46,0.02, 0.105,0.12,0.11, skin);
          sphere(rightCalf, 0,-0.51,0.10, 0.15,0.085,0.23, shoes);

          // Braços segurando a barra
          limb(athlete, [-0.39,2.02,0], [-0.59,1.91,0.10], 0.105, skin);
          limb(athlete, [-0.59,1.91,0.10], [-0.49,2.25,0.18], 0.085, skin);
          limb(athlete, [0.39,2.02,0], [0.59,1.91,0.10], 0.105, skin);
          limb(athlete, [0.59,1.91,0.10], [0.49,2.25,0.18], 0.085, skin);

          // Barra horizontal apoiada nos ombros
          const bar = cylinder(athlete, 0, 2.28, 0, 0.045, 2.45, steel);
          bar.rotation.z = Math.PI / 2;

          // Anilhas dos dois lados da barra
          [-1, 1].forEach(side => {
            for (let i = 0; i < 3; i++) {
              const x = side * (0.86 + i * 0.14);

              const plate = cylinder(
                athlete, x, 2.28, 0, 0.22 - i*0.015, 0.10, plateMat
              );
              plate.rotation.z = Math.PI / 2;

              const center = cylinder(
                athlete, x, 2.28, 0.01, 0.055, 0.105, steel
              );
              center.rotation.z = Math.PI / 2;
            }
          });

          // Luzes decorativas no chão
          const ring = new THREE.Mesh(
            new THREE.TorusGeometry(1.0, 0.012, 8, 64),
            mat(0x913fff, 0.3, 0.4)
          );
          ring.rotation.x = Math.PI / 2;
          ring.position.y = 0.015;
          ring.scale.set(1.3, 0.7, 1);
          scene.add(ring);

          // Estado do jogo
          let reps = 0;
          let isDown = false;
          let targetDown = false;
          let last = performance.now();

          function updateStats() {
            document.getElementById("reps").textContent = reps + " / 40";
            document.getElementById("series").textContent =
              (reps >= 40 ? 4 : Math.floor(reps / 10) + 1) + " / 4";
            document.getElementById("bio").textContent =
              (reps * 0.005).toFixed(3);
            document.getElementById("fill").style.width =
              (reps / 40 * 100) + "%";

            document.getElementById("message").textContent =
              reps >= 40 ? "🏆 Treino concluído!" :
              reps > 0 ? "Boa! Continue treinando." :
              "Pronto para começar!";
          }

          document.getElementById("down").addEventListener("click", () => {
            if (reps >= 40 || isDown) return;
            isDown = true;
            targetDown = true;
            document.getElementById("message").textContent =
              "Desça com controle...";
          });

          document.getElementById("rise").addEventListener("click", () => {
            if (!isDown || reps >= 40) return;

            isDown = false;
            targetDown = false;
            reps++;
            updateStats();
          });

          document.getElementById("reset").addEventListener("click", () => {
            reps = 0;
            isDown = false;
            targetDown = false;
            athlete.position.y = 0;
            leftLeg.rotation.x = 0;
            rightLeg.rotation.x = 0;
            leftCalf.rotation.x = 0;
            rightCalf.rotation.x = 0;
            updateStats();
          });

          // Animação 3D
          function animate(now) {
            requestAnimationFrame(animate);

            const dt = Math.min((now - last) / 1000, 0.05);
            last = now;

            const downY = targetDown ? -0.32 : 0;
            athlete.position.y +=
              (downY - athlete.position.y) * Math.min(1, dt * 5);

            const thighAngle = targetDown ? 0.30 : 0;
            const kneeAngle = targetDown ? -0.58 : 0;

            leftLeg.rotation.x +=
              (thighAngle - leftLeg.rotation.x) * Math.min(1, dt * 5);
            rightLeg.rotation.x +=
              (thighAngle - rightLeg.rotation.x) * Math.min(1, dt * 5);

            leftCalf.rotation.x +=
              (kneeAngle - leftCalf.rotation.x) * Math.min(1, dt * 5);
            rightCalf.rotation.x +=
              (kneeAngle - rightCalf.rotation.x) * Math.min(1, dt * 5);

            renderer.render(scene, camera);
          }

          function resizeGame() {
            const width = holder.clientWidth;
            const height = holder.clientHeight;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
          }

          window.addEventListener("resize", resizeGame);

          updateStats();
          requestAnimationFrame(animate);
        })();
        </script>
        </body>
        </html>
        """,
        height=650,
        scrolling=False,
    )



# =========================================================
# EXECUÇÃO PRINCIPAL
# =========================================================

mostrar_cabecalho()
mostrar_botao_sair()


# ADMIN LOGADO
if st.session_state.admin:
    mostrar_admin()
    st.stop()


# PARTICIPANTE LOGADO
if st.session_state.participante:
    mostrar_participante()
    st.stop()


# NINGUÉM LOGADO
mostrar_login_admin()
mostrar_login_cadastro()
