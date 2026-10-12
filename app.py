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

    # JOGO DE AGACHAMENTO BIOCORE
    if st.button("🏋️ Jogar agachamento 3D"):
        st.session_state["abrir_jogo_agachamento"] = True

    if st.session_state.get("abrir_jogo_agachamento", False):
        mostrar_jogo_agachamento()

    bio = int(
        participante.get("bio", 0) or 0
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

        

def mostrar_jogo_agachamento():
    st.components.v1.html(
        """
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
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
            background: linear-gradient(160deg,#29253d,#11121b);
            border: 1px solid #49405f;
            border-radius: 18px;
          }
          h2 { text-align:center; font-size:20px; }
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
            <div class="stat">SÉRIE<strong id="series">1 / 4</strong></div>
            <div class="stat">REPETIÇÕES<strong id="reps">0 / 40</strong></div>
            <div class="stat">BIO ESTIMADO<strong id="bio">0.000</strong></div>
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
            O contador não deposita BIO na carteira.
          </div>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script>
        (() => {
          const holder = document.getElementById("scene");

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
          camera.position.set(0.2, 2.5, 8.5);
          camera.lookAt(0, 1.3, 0);

          const renderer = new THREE.WebGLRenderer({antialias:true});
          renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
          renderer.setSize(holder.clientWidth, holder.clientHeight);
          renderer.outputEncoding = THREE.sRGBEncoding;
          holder.appendChild(renderer.domElement);

          scene.add(new THREE.HemisphereLight(0xdde5ff, 0x302039, 2));

          const light = new THREE.DirectionalLight(0xffffff, 2.5);
          light.position.set(-3, 7, 5);
          scene.add(light);

          const glow = new THREE.PointLight(0xb34cff, 2);
          glow.position.set(3, 3, 2);
          scene.add(glow);

          function mat(color, metalness=0, roughness=0.55) {
            return new THREE.MeshStandardMaterial({
              color: color,
              metalness: metalness,
              roughness: roughness
            });
          }

          const skin = mat(0xc98d69);
          const shirt = mat(0x8537d0);
          const shorts = mat(0x25273b);
          const shoes = mat(0xe4e7f4);
          const steel = mat(0xc3cad6,0.85,0.25);
          const plateMat = mat(0x252735,0.45,0.3);

          const floor = new THREE.Mesh(
            new THREE.PlaneGeometry(30,30),
            mat(0x22243a)
          );
          floor.rotation.x = -Math.PI/2;
          floor.position.y = -0.03;
          scene.add(floor);

          const grid = new THREE.GridHelper(20,20,0x51446e,0x303047);
          grid.position.y = -0.015;
          scene.add(grid);

          function sphere(parent,x,y,z,sx,sy,sz,material) {
            const mesh = new THREE.Mesh(
              new THREE.SphereGeometry(1,24,16), material
            );
            mesh.position.set(x,y,z);
            mesh.scale.set(sx,sy,sz);
            parent.add(mesh);
            return mesh;
          }

          function cylinder(parent,x,y,z,radius,length,material) {
            const mesh = new THREE.Mesh(
              new THREE.CylinderGeometry(radius,radius,length,24),material
            );
            mesh.position.set(x,y,z);
            parent.add(mesh);
            return mesh;
          }

          function limb(parent,a,b,radius,material) {
            const start = new THREE.Vector3(...a);
            const end = new THREE.Vector3(...b);
            const direction = new THREE.Vector3().subVectors(end,start);
            const mesh = new THREE.Mesh(
              new THREE.CylinderGeometry(
                radius*0.8,radius,direction.length(),20
              ),material
            );
            mesh.position.copy(start).add(end).multiplyScalar(0.5);
            mesh.quaternion.setFromUnitVectors(
              new THREE.Vector3(0,1,0),direction.normalize()
            );
            parent.add(mesh);
            return mesh;
          }

          // Corpo do atleta
          const athlete = new THREE.Group();
          scene.add(athlete);

          sphere(athlete,0,1.78,0,0.44,0.55,0.28,shirt);
          sphere(athlete,0,1.99,0.13,0.38,0.25,0.21,shirt);
          cylinder(athlete,0,2.30,0,0.11,0.15,skin);
          sphere(athlete,0,2.53,0,0.23,0.26,0.22,skin);
          sphere(athlete,-0.075,2.56,0.202,0.025,0.025,0.012,plateMat);
          sphere(athlete,0.075,2.56,0.202,0.025,0.025,0.012,plateMat);
          sphere(athlete,0,1.22,0,0.38,0.23,0.24,shorts);

          // Perna esquerda e joelho
          const leftLeg = new THREE.Group();
          leftLeg.position.set(-0.21,1.15,0);
          athlete.add(leftLeg);
          limb(leftLeg,[0,0,0],[0,-0.47,0],0.145,skin);
          sphere(leftLeg,0,-0.47,0,0.14,0.14,0.14,skin);

          const leftCalf = new THREE.Group();
          leftCalf.position.set(0,-0.47,0);
          leftLeg.add(leftCalf);
          limb(leftCalf,[0,0,0],[0,-0.47,0],0.10,skin);
          sphere(leftCalf,0,-0.46,0.02,0.105,0.12,0.11,skin);
          sphere(leftCalf,0,-0.51,0.10,0.15,0.085,0.23,shoes);

          // Perna direita e joelho
          const rightLeg = new THREE.Group();
          rightLeg.position.set(0.21,1.15,0);
          athlete.add(rightLeg);
          limb(rightLeg,[0,0,0],[0,-0.47,0],0.145,skin);
          sphere(rightLeg,0,-0.47,0,0.14,0.14,0.14,skin);

          const rightCalf = new THREE.Group();
          rightCalf.position.set(0,-0.47,0);
          rightLeg.add(rightCalf);
          limb(rightCalf,[0,0,0],[0,-0.47,0],0.10,skin);
          sphere(rightCalf,0,-0.46,0.02,0.105,0.12,0.11,skin);
          sphere(rightCalf,0,-0.51,0.10,0.15,0.085,0.23,shoes);

          // Braços
          limb(athlete,[-0.39,2.02,0],[-0.59,1.91,0.10],0.105,skin);
          limb(athlete,[-0.59,1.91,0.10],[-0.49,2.25,0.18],0.085,skin);
          limb(athlete,[0.39,2.02,0],[0.59,1.91,0.10],0.105,skin);
          limb(athlete,[0.59,1.91,0.10],[0.49,2.25,0.18],0.085,skin);

          // Barra e anilhas
          const bar = cylinder(athlete,0,2.28,0,0.045,2.45,steel);
          bar.rotation.z = Math.PI/2;

          [-1,1].forEach(side => {
            for (let i=0;i<3;i++) {
              const x = side*(0.86+i*0.14);
              const plate = cylinder(
                athlete,x,2.28,0,0.22-i*0.015,0.10,plateMat
              );
              plate.rotation.z = Math.PI/2;
              const center = cylinder(
                athlete,x,2.28,0.01,0.055,0.105,steel
              );
              center.rotation.z = Math.PI/2;
            }
          });

          
          // Controles e repetições
          let reps = 0;
          let isDown = false;
          let targetDown = false;
          let last = performance.now();

          function updateStats() {
            document.getElementById("reps").textContent = reps+" / 40";
            document.getElementById("series").textContent =
              (reps>=40 ? 4 : Math.floor(reps/10)+1)+" / 4";
            document.getElementById("bio").textContent =
              (reps*0.005).toFixed(3);
            document.getElementById("fill").style.width =
              (reps/40*100)+"%";
            document.getElementById("message").textContent =
              reps>=40 ? "🏆 Treino concluído!" :
              reps>0 ? "Boa! Continue treinando." :
              "Pronto para começar!";
          }

          document.getElementById("down").addEventListener("click",() => {
            if (reps>=40 || isDown) return;
            isDown = true;
            targetDown = true;
            document.getElementById("message").textContent =
              "Desça com controle...";
          });

          document.getElementById("rise").addEventListener("click",() => {
            if (!isDown || reps>=40) return;
            isDown = false;
            targetDown = false;
            reps++;
            updateStats();
          });

          document.getElementById("reset").addEventListener("click",() => {
            reps = 0;
            isDown = false;
            targetDown = false;
            updateStats();
          });


          
          function animate(now) {
            requestAnimationFrame(animate);

            const dt = Math.min((now - last) / 1000, 0.05);
            last = now;

            const t = targetDown ? 1 : 0;
            const smooth = t * t * (3 - 2 * t);

            // Agachamento mais profundo
            const thighAngle = -1.70 * smooth;
            const calfAngle = 1.32 * smooth;

            leftLeg.rotation.x +=
              (thighAngle - leftLeg.rotation.x) *
              Math.min(1, dt * 8);

            rightLeg.rotation.x +=
              (thighAngle - rightLeg.rotation.x) *
              Math.min(1, dt * 8);

            leftCalf.rotation.x +=
              (calfAngle - leftCalf.rotation.x) *
              Math.min(1, dt * 8);

            rightCalf.rotation.x +=
              (calfAngle - rightCalf.rotation.x) *
              Math.min(1, dt * 8);

            // Quadril desce sem afundar tanto o personagem
            const bodyY = -0.28 * smooth;
            athlete.position.y +=
              (bodyY - athlete.position.y) *
              Math.min(1, dt * 6);

            renderer.render(scene, camera);
          }
          


          function resizeGame() {
            const w = holder.clientWidth;
            const h = holder.clientHeight;
            camera.aspect = w/h;
            camera.updateProjectionMatrix();
            renderer.setSize(w,h);
          }

          window.addEventListener("resize",resizeGame);
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
