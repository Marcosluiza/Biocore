import streamlit as st
import requests
import hashlib
import secrets
import binascii
from datetime import datetime, timedelta, timezone

# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="BioCore",
    page_icon="💪",
    layout="centered"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

BUCKET = "Comprovacoes"

BIO_TREINO = 10
BIO_FOTO = 70
LIMITE_BIO = 5000
VALOR_BIO = 0.01

# =========================
# FUNÇÕES DE SENHA
# =========================

def hash_password(password):
    salt = secrets.token_bytes(16)

    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        200000
    )

    return (
        f"{binascii.hexlify(salt).decode()}"
        f"${binascii.hexlify(pwd_hash).decode()}"
    )


def verify_password(password, stored):
    try:
        salt_hex, hash_hex = stored.split("$")

        salt = binascii.unhexlify(salt_hex)

        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            200000
        )

        return secrets.compare_digest(
            binascii.hexlify(pwd_hash).decode(),
            hash_hex
        )

    except Exception:
        return False


# =========================
# SUPABASE
# =========================

def supabase_get(tabela, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    resposta = requests.get(
        url,
        headers=HEADERS,
        params=params or {}
    )

    if resposta.status_code >= 400:
        st.error(f"Erro Supabase: {resposta.text}")
        return []

    return resposta.json()


def supabase_insert(tabela, dados):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    headers = HEADERS.copy()
    headers["Prefer"] = "return=representation"

    resposta = requests.post(
        url,
        headers=headers,
        json=dados
    )

    if resposta.status_code >= 400:
        st.error(f"Erro Supabase: {resposta.text}")
        return []

    return resposta.json()


def supabase_update(tabela, dados, params):
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    headers = HEADERS.copy()
    headers["Prefer"] = "return=representation"

    resposta = requests.patch(
        url,
        headers=headers,
        params=params,
        json=dados
    )

    if resposta.status_code >= 400:
        st.error(f"Erro Supabase: {resposta.text}")
        return []

    return resposta.json()


# =========================
# STORAGE
# =========================

def enviar_foto_storage(caminho, arquivo):
    url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"{BUCKET}/{caminho}"
    )

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": arquivo.type
    }

    resposta = requests.post(
        url,
        headers=headers,
        data=arquivo.getvalue()
    )

    return resposta


def baixar_foto_storage(caminho):
    url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"{BUCKET}/{caminho}"
    )

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY
    }

    resposta = requests.get(
        url,
        headers=headers
    )

    if resposta.status_code == 200:
        return resposta.content

    return None


# =========================
# SESSÃO
# =========================

if "participante" not in st.session_state:
    st.session_state.participante = None

if "admin" not in st.session_state:
    st.session_state.admin = False


# =========================
# LOGO / TÍTULO
# =========================

st.title("💪 BioCore")

st.write(
    "Treine, registre suas atividades e acumule BIO."
)

st.divider()


# =========================
# ADMIN
# =========================

with st.expander("🔐 Login administrativo"):

    if not st.session_state.admin:

        senha_admin = st.text_input(
            "Senha administrativa",
            type="password"
        )

        if st.button("Entrar como administrador"):

            # Temporariamente usamos a senha antiga.
            # Depois vamos colocar a senha administrativa
            # também nos Secrets.
            if senha_admin == "1234":

                st.session_state.admin = True
                st.rerun()

            else:
                st.error("Senha administrativa incorreta.")

    else:

        st.success("Administrador conectado.")

        if st.button("Sair do administrador"):
            st.session_state.admin = False
            st.rerun()


# =========================
# PAINEL ADMIN
# =========================

if st.session_state.admin:

    st.header("Painel administrativo")

    participantes = supabase_get(
        "participantes",
        {
            "select": "*",
            "order": "created_at.desc"
        }
    )

    st.subheader("Participantes")

    if not participantes:
        st.info("Nenhum participante cadastrado.")

    else:

        for pessoa in participantes:

            with st.container():

                st.markdown(
                    f"### {pessoa['nome']}"
                )

                st.write(
                    f"📧 {pessoa['email']}"
                )

                st.write(
                    f"💰 BIO: {pessoa.get('bio', 0)}"
                )

                st.write("---")

    st.subheader("📸 Comprovações")

    comprovacoes = supabase_get(
        "comprovacoes",
        {
            "select": "*",
            "order": "created_at.desc"
        }
    )

    if not comprovacoes:

        st.info("Nenhuma comprovação enviada.")

    else:

        for comprovacao in comprovacoes:

            participante_id = comprovacao["participante_id"]

            pessoa = supabase_get(
                "participantes",
                {
                    "select": "nome,email",
                    "id": f"eq.{participante_id}",
                    "limit": "1"
                }
            )

            nome = (
                pessoa[0]["nome"]
                if pessoa
                else "Participante"
            )

            st.markdown(
                f"### 📸 {nome}"
            )

            st.write(
                f"Arquivo: {comprovacao['nome_arquivo']}"
            )

            st.write(
                f"Status: {comprovacao['status']}"
            )

            imagem = baixar_foto_storage(
                comprovacao["arquivo_path"]
            )

            if imagem:
                st.image(
                    imagem,
                    use_container_width=True
                )

            if (
                comprovacao["status"] == "Pendente"
                and not comprovacao["bio_pago"]
            ):

                if st.button(
                    "✅ Aprovar +70 BIO",
                    key=f"aprovar_{comprovacao['id']}"
                ):

                    participante = supabase_get(
                        "participantes",
                        {
                            "select": "bio",
                            "id": f"eq.{participante_id}",
                            "limit": "1"
                        }
                    )

                    if participante:

                        bio_atual = participante[0].get(
                            "bio", 0
                        ) or 0

                        novo_bio = bio_atual + BIO_FOTO

                        supabase_update(
                            "participantes",
                            {"bio": novo_bio},
                            {
                                "id": f"eq.{participante_id}"
                            }
                        )

                        supabase_update(
                            "comprovacoes",
                            {
                                "status": "Aprovada",
                                "bio_pago": True
                            },
                            {
                                "id": f"eq.{comprovacao['id']}"
                            }
                        )

                        st.success(
                            "Comprovação aprovada e +70 BIO adicionados."
                        )

                        st.rerun()

            st.divider()

    st.stop()


# =========================
# PARTICIPANTE LOGADO
# =========================

if st.session_state.participante:

    participante = st.session_state.participante

    # Atualiza dados do banco
    dados = supabase_get(
        "participantes",
        {
            "select": "*",
            "id": f"eq.{participante['id']}",
            "limit": "1"
        }
    )

    if dados:
        participante = dados[0]
        st.session_state.participante = participante

    st.header(
        f"Olá, {participante['nome']}! 👋"
    )

    bio_atual = participante.get("bio", 0) or 0

    st.metric(
        "💰 Meu saldo BIO",
        f"{bio_atual:,}".replace(",", ".")
    )

    st.write(
        f"Cashback disponível ao atingir "
        f"{LIMITE_BIO:,} BIO: até R$ 50,00"
    )

    st.divider()

    # =========================
    # REGISTRAR TREINO
    # =========================

    st.subheader("🏋️ Registrar atividade")

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
        ]
    )

    if st.button("Registrar treino"):

        supabase_insert(
            "treinos",
            {
                "participante_id": participante["id"],
                "atividade": atividade,
                "status": "Registrado"
            }
        )

        novo_bio = bio_atual + BIO_TREINO

        supabase_update(
            "participantes",
            {"bio": novo_bio},
            {
                "id": f"eq.{participante['id']}"
            }
        )

        st.session_state.participante["bio"] = novo_bio

        st.success(
            f"Treino registrado! +{BIO_TREINO} BIO"
        )

        st.rerun()

    st.divider()

    # =========================
    # FOTO SEMANAL
    # =========================

    st.subheader("📸 Comprovação semanal")

    st.write(
        "Envie uma foto do seu treino. "
        "Após aprovação administrativa, você recebe +70 BIO."
    )

    agora = datetime.now(timezone.utc)

    ultima = supabase_get(
        "comprovacoes",
        {
            "select": "created_at",
            "participante_id": f"eq.{participante['id']}",
            "order": "created_at.desc",
            "limit": "1"
        }
    )

    pode_enviar = True

    if ultima:

        try:
            data_ultima = datetime.fromisoformat(
                ultima[0]["created_at"].replace(
                    "Z", "+00:00"
                )
            )

            if agora - data_ultima < timedelta(days=7):
                pode_enviar = False

        except Exception:
            pass

    if not pode_enviar:

        st.info(
            "Você já enviou uma comprovação nos últimos 7 dias."
        )

    else:

        foto = st.file_uploader(
            "Escolha a foto",
            type=["jpg", "jpeg", "png"]
        )

        if foto:

            st.image(
                foto,
                caption="Foto selecionada",
                use_container_width=True
            )

            if st.button("Enviar comprovação"):

                nome_original = foto.name

                caminho = (
                    f"{participante['id']}/"
                    f"{int(datetime.now().timestamp())}_"
                    f"{nome_original}"
                )

                resposta = enviar_foto_storage(
                    caminho,
                    foto
                )

                if resposta.status_code in [200, 201]:

                    supabase_insert(
                        "comprovacoes",
                        {
                            "participante_id": participante["id"],
                            "nome_arquivo": nome_original,
                            "arquivo_path": caminho,
                            "tipo": foto.type,
                            "status": "Pendente",
                            "bio_pago": False
                        }
                    )

                    st.success(
                        "Comprovação enviada! "
                        "Aguarde a aprovação."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Não foi possível enviar a foto."
                    )

    st.divider()

    # =========================
    # TRUST WALLET
    # =========================

    st.subheader("👛 Minha Trust Wallet")

    wallet = st.text_input(
        "Endereço da carteira",
        value=participante.get("wallet", "")
    )

    if st.button("Salvar carteira"):

        supabase_update(
            "participantes",
            {"wallet": wallet},
            {
                "id": f"eq.{participante['id']}"
            }
        )

        st.session_state.participante["wallet"] = wallet

        st.success("Carteira salva.")

    st.divider()

    # =========================
    # CASHBACK
    # =========================

    st.subheader("💵 Cashback")

    if bio_atual >= LIMITE_BIO:

        st.success(
            "Você atingiu 5.000 BIO."
        )

        st.write(
            "Valor máximo disponível neste ciclo: R$ 50,00."
        )

        if not participante.get(
            "cashback_solicitado", False
        ):

            if st.button("Solicitar cashback"):

                supabase_update(
                    "participantes",
                    {
                        "cashback_solicitado": True
                    },
                    {
                        "id": f"eq.{participante['id']}"
                    }
                )

                st.success(
                    "Solicitação enviada ao administrador."
                )

                st.rerun()

        else:

            st.info(
                "Seu cashback já foi solicitado."
            )

    else:

        faltam = LIMITE_BIO - bio_atual

        st.info(
            f"Faltam {faltam:,} BIO para atingir 5.000."
            .replace(",", ".")
        )

    st.divider()

    # =========================
    # LINKS
    # =========================

    st.subheader("🛍️ Parceiros")

    st.link_button(
        "🛒 Mercado Livre",
        "https://www.mercadolivre.com.br/social/sama6231844"
    )

    st.link_button(
        "🏪 CoreStryke",
        "https://corestryke.com"
    )

    st.divider()

    if st.button("Sair"):

        st.session_state.participante = None
        st.rerun()

    st.stop()


# =========================
# TELA DE LOGIN / CADASTRO
# =========================

aba = st.radio(
    "Escolha uma opção",
    [
        "Entrar",
        "Criar cadastro"
    ],
    horizontal=True
)


# =========================
# LOGIN
# =========================

if aba == "Entrar":

    st.subheader("🔑 Entrar")

    email = st.text_input("E-mail")

    senha = st.text_input(
        "Senha",
        type="password"
    )

    if st.button("Entrar"):

        if not email or not senha:

            st.warning(
                "Preencha e-mail e senha."
            )

        else:

            resultado = supabase_get(
                "participantes",
                {
                    "select": "*",
                    "email": f"eq.{email.strip().lower()}",
                    "limit": "1"
                }
            )

            if resultado:

                pessoa = resultado[0]

                if verify_password(
                    senha,
                    pessoa["senha_hash"]
                ):

                    st.session_state.participante = pessoa

                    st.success(
                        "Login realizado!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "E-mail ou senha incorretos."
                    )

            else:

                st.error(
                    "E-mail ou senha incorretos."
                )


# =========================
# CADASTRO
# =========================

else:

    st.subheader("📝 Criar cadastro")

    nome = st.text_input("Nome")

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

    if st.button("Criar cadastro"):

        if not nome or not email or not senha:

            st.warning(
                "Preencha todos os campos."
            )

        elif senha != confirmar:

            st.error(
                "As senhas não são iguais."
            )

        else:

            email_limpo = email.strip().lower()

            existente = supabase_get(
                "participantes",
                {
                    "select": "id",
                    "email": f"eq.{email_limpo}",
                    "limit": "1"
                }
            )

            if existente:

                st.error(
                    "Este e-mail já está cadastrado."
                )

            else:

                novo = supabase_insert(
                    "participantes",
                    {
                        "nome": nome.strip(),
                        "email": email_limpo,
                        "senha_hash": hash_password(senha),
                        "wallet": "",
                        "bio": 0,
                        "cashback_solicitado": False,
                        "cashback_pago": False
                    }
                )

                if novo:

                    st.success(
                        "Cadastro criado com sucesso!"
                    )

                    st.info(
                        "Agora vá em 'Entrar' para acessar."
                    )
