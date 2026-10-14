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

        # ROLETA DA SORTE BIOCORE
    mostrar_roleta_biocore(participante)

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
    
 



def mostrar_roleta_biocore(participante):
    import random
    from datetime import datetime
    from zoneinfo import ZoneInfo
    import streamlit.components.v1 as components

    email = str(participante.get("email", "")).strip().lower()

    if not email:
        st.error("Não foi possível identificar sua conta.")
        return

    hoje = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).date().isoformat()

    dados = supabase_get("roleta_diaria", {
        "select": "*",
        "email": f"eq.{email}",
        "data_giro": f"eq.{hoje}",
        "limit": "1",
    })

    if dados is None:
        st.error("Não foi possível consultar os giros.")
        return

    registro = dados[0] if dados else None
    usados = int(registro.get("giros_usados", 0)) if registro else 0

    st.subheader("🎡 Roleta da Sorte BioCore")
    st.write("Gire a roleta e concorra a BIO!")
    st.write(f"🎟️ Giros usados hoje: **{usados}/3**")

    premios = [
        ("1 BIO", 1),
        ("2 BIO", 2),
        ("5 BIO", 5),
        ("10 BIO", 10),
        ("25 BIO", 25),
        ("50 BIO", 50),
        ("100 BIO", 100),
        ("Tente novamente", 0),
    ]

    probabilidades = [20, 20, 16, 15, 12, 10, 1, 6]

    cores = [
        "#E84393", "#8E44AD", "#3498DB", "#16A085",
        "#F39C12", "#E74C3C", "#6C5CE7", "#55516B"
    ]

    if usados < 3:
        if st.button("🎡 GIRAR A ROLETA", key="girar_roleta_biocore"):
            premio_nome, premio_bio = random.choices(
                premios,
                weights=probabilidades,
                k=1,
            )[0]

            bio_atual = int(participante.get("bio", 0) or 0)
            novo_saldo = bio_atual + premio_bio

            if registro:
                resultado = supabase_update(
                    "roleta_diaria",
                    {
                        "email": f"eq.{email}",
                        "data_giro": f"eq.{hoje}",
                    },
                    {
                        "giros_usados": usados + 1,
                        "bio_ganho": int(registro.get("bio_ganho", 0) or 0) + premio_bio,
                    },
                )
            else:
                resultado = supabase_insert(
                    "roleta_diaria",
                    {
                        "email": email,
                        "data_giro": hoje,
                        "giros_usados": 1,
                        "bio_ganho": premio_bio,
                    },
                )

            if resultado is None or resultado is False:
                st.error("Não foi possível registrar o giro. Tente novamente.")
                return

            if premio_bio > 0:
                saldo_salvo = supabase_update(
                    "participantes",
                    {"id": f"eq.{participante['id']}"},
                    {"bio": novo_saldo},
                )

                if saldo_salvo is None or saldo_salvo is False:
                    st.error(
                        "O giro foi registrado, mas não conseguimos "
                        "atualizar o saldo. Procure o administrador "
                        "antes de tentar novamente."
                    )
                    return

            st.session_state["resultado_roleta"] = {
                "nome": premio_nome,
                "bio": premio_bio,
                "email": email,
                "data": hoje,
            }

            st.rerun()

    else:
        st.info("Você já usou os 3 giros de hoje. Volte amanhã!")

    resultado = st.session_state.get("resultado_roleta")

    if resultado and resultado.get("email") == email and resultado.get("data") == hoje:
        st.success(f"🎉 Resultado do giro: {resultado['nome']}!")

    # Roleta visual com animação e som
    import json

    textos = [p[0] for p in premios]
    cores_json = json.dumps(cores)
    textos_json = json.dumps(textos)

    resultado_indice = None
    if resultado and resultado.get("email") == email and resultado.get("data") == hoje:
        nome_resultado = resultado["nome"]
        resultado_indice = textos.index(nome_resultado)

    indice_json = json.dumps(resultado_indice)

    components.html(
        """
        <div style="background:#17151f;color:white;padding:16px;
                    border-radius:18px;text-align:center;font-family:Arial">
          <div style="position:relative;width:280px;height:280px;
                      max-width:85vw;margin:12px auto">
            <div style="position:absolute;top:-5px;left:calc(50% - 14px);
                        z-index:3;width:0;height:0;
                        border-left:14px solid transparent;
                        border-right:14px solid transparent;
                        border-top:28px solid white"></div>
            
<div id="roda" style="width:100%;height:100%;border-radius:50%;
                 border:5px solid white;box-sizing:border-box;
                 background:conic-gradient(
                   #E84393 0deg 45deg,#8E44AD 45deg 90deg,
                   #3498DB 90deg 135deg,#16A085 135deg 180deg,
                   #F39C12 180deg 225deg,#E74C3C 225deg 270deg,
                   #6C5CE7 270deg 315deg,#55516B 315deg 360deg);
                 transition:transform 4s cubic-bezier(.12,.72,.12,1);
                 position:relative">
</div>
            
            
            </div>

            </div>

            
            
           <div id="numeros_roleta" style="position:absolute;inset:0;pointer-events:none;color:white;font-weight:bold;text-align:center;">
              <div style="position:absolute;top:18%;left:33%;width:16%;font-size:12px;">1 BIO</div>
              <div style="position:absolute;top:13%;right:28%;width:25%;font-size:12px;">2 BIO</div>
              <div style="position:absolute;top:43%;right:8%;width:25%;font-size:12px;">5 BIO</div>
              <div style="position:absolute;top:62%;right:8%;width:25%;font-size:12px;">10 BIO</div>
              <div style="position:absolute;bottom:10%;left:39%;width:25%;font-size:12px;">25 BIO</div>
              <div style="position:absolute;bottom:10%;left:8%;width:25%;font-size:12px;">50 BIO</div>
              <div style="position:absolute;top:62%;left:7%;width:25%;font-size:12px;">100 BIO</div>
           <div style="position:absolute;top:40%;left:3%;width:30%;font-size:10px;">Tente de novo</div>
            </div>

          </div>
          
          <p id="mensagem">Boa sorte! 🍀</p>
          <button id="som" style="background:#E84393;color:white;
             border:0;border-radius:10px;padding:10px 16px">
             🔊 Ativar som
          </button>
        </div>
        <script>
        const indice = __INDICE__;
        const roda = document.getElementById('roda');
        const numeros = document.getElementById('numeros_roleta');
        const mensagem = document.getElementById('mensagem');
        let audio = null;
        let somAtivo = false;

        document.getElementById('som').onclick = () => {
          audio = new (window.AudioContext || window.webkitAudioContext)();
          audio.resume();
          somAtivo = true;
          mensagem.textContent = 'Som ativado! 🔊';
        };

        function bip(freq, duracao) {
          if (!somAtivo || !audio) return;
          const o = audio.createOscillator();
          const g = audio.createGain();
          o.frequency.value = freq;
          g.gain.value = 0.04;
          o.connect(g);
          g.connect(audio.destination);
          o.start();
          o.stop(audio.currentTime + duracao);
        }
        
        if (indice !== null) {
  const angulo = 360 * 6 + (360 - (indice * 45 + 22.5));

  const quadros = [
    { transform: 'rotate(0deg)' },
    { transform: 'rotate(' + angulo + 'deg)' }
  ];

  const configuracao = {
    duration: 4000,
    easing: 'cubic-bezier(.12,.72,.12,1)',
    fill: 'forwards'
  };

  roda.style.transform = '';
  numeros.style.transform = '';

  roda.animate(quadros, configuracao);
  numeros.animate(quadros, configuracao);
}


        
          let cliques = 0;
          const somGiro = setInterval(() => {
            bip(500 + (cliques % 4) * 100, 0.035);
            cliques++;
          }, 180);
          setTimeout(() => {
            clearInterval(somGiro);
            bip(880, 0.22);
            mensagem.textContent = '🎉 Giro concluído!';
          }, 4100);
        </script>
        """.replace("__INDICE__", indice_json),
        height=365,
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
