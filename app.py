import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="BioCore",
    page_icon="🪙",
    layout="centered"
)

LIMITE_BIO = 5000
VALOR_BIO = 0.01

BIO_TREINO = 10
BIO_FOTO = 70

SENHA_ADMIN = "1234"

ATIVIDADES = [
    "Peito, ombro e tríceps",
    "Costas e bíceps",
    "Quadríceps, glúteos e panturrilhas",
    "Perna completo",
    "Abdômen",
    "Peso corporal",
    "Corrida",
    "Futebol"
]


# ============================================================
# MEMÓRIA
# ============================================================

if "usuarios" not in st.session_state:
    st.session_state.usuarios = {}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = ""

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False


# ============================================================
# TÍTULO
# ============================================================

st.title("🪙 BioCore")
st.write("Seu desafio. Seu BIO. Seu cashback.")


# ============================================================
# PARTICIPANTE LOGADO
# ============================================================

if st.session_state.usuario_logado != "":

    email = st.session_state.usuario_logado
    dados = st.session_state.usuarios[email]

    nome = dados["nome"]

    st.success("Olá, " + nome + "! 👋")

    if st.button(
        "🚪 Sair da conta",
        use_container_width=True
    ):
        st.session_state.usuario_logado = ""
        st.rerun()

    st.divider()

    # ========================================================
    # CASHBACK
    # ========================================================

    st.header("💰 Meu Cashback")

    bio = dados["bio"]

    bio_exibido = min(bio, LIMITE_BIO)

    cashback = bio_exibido * VALOR_BIO

    cashback = min(cashback, 50)

    porcentagem = bio_exibido / LIMITE_BIO

    st.markdown(
        "<div style='background:#f3f3f3;padding:20px;border-radius:15px;'>"
        "<div>Cashback disponível</div>"
        "<div style='font-size:32px;font-weight:bold;'>"
        "R$ " + format(cashback, ".2f") +
        "</div>"
        "<div style='width:100%;height:18px;background:#ddd;border-radius:10px;'>"
        "<div style='width:" + str(porcentagem * 100) +
        "%;height:18px;background:#20c997;border-radius:10px;'></div>"
        "</div>"
        "<p><strong>" +
        format(bio_exibido, ",") +
        " / " +
        format(LIMITE_BIO, ",") +
        " BIO</strong></p>"
        "</div>",
        unsafe_allow_html=True
    )

    if bio < LIMITE_BIO:

        faltam = LIMITE_BIO - bio

        st.write(
            "Faltam " +
            format(faltam, ",") +
            " BIO para chegar a R$50,00."
        )

    else:

        st.success(
            "🎉 Você atingiu R$50,00 de cashback."
        )


    # ========================================================
    # TREINO / ATIVIDADE FÍSICA
    # ========================================================

    st.divider()

    st.header("🏋️ Treino / Atividade Física")

    st.write(
        "O que você treinou hoje?"
    )

    atividade = st.selectbox(
        "Escolha uma atividade",
        ATIVIDADES
    )

    st.caption(
        "Registre somente um treino por vez."
    )

    if st.button(
        "➕ Registrar treino +10 BIO",
        use_container_width=True
    ):

        registro = {
            "atividade": atividade,
            "status": "Registrado"
        }

        dados["treinos_lista"].append(registro)

        dados["bio"] += BIO_TREINO

        dados["treinos"] += 1

        st.success(
            "Treino registrado: " +
            atividade +
            " | +10 BIO"
        )

        st.rerun()


    # ========================================================
    # HISTÓRICO DE TREINOS
    # ========================================================

    if len(dados["treinos_lista"]) > 0:

        st.subheader("📋 Meus treinos")

        for treino in reversed(dados["treinos_lista"]):

            st.write(
                "🏋️ " + treino["atividade"]
            )


    # ========================================================
    # COMPROVAÇÃO
    # ========================================================

    st.divider()

    st.header("📸 Comprovação semanal")

    st.write(
        "Envie uma foto para comprovar seu treino."
    )

    foto = st.file_uploader(
        "Selecionar foto",
        type=["jpg", "jpeg", "png"],
        key="foto_upload"
    )

    if foto is not None:

        if st.button(
            "📤 Enviar foto para análise",
            use_container_width=True
        ):

            comprovacao = {
                "nome_arquivo": foto.name,
                "status": "Pendente",
                "bio_pago": False
            }

            dados["comprovacoes"].append(
                comprovacao
            )

            st.success(
                "Foto enviada! Status: 🟡 Pendente"
            )

            st.rerun()


    # ========================================================
    # STATUS DAS COMPROVAÇÕES
    # ========================================================

    if len(dados["comprovacoes"]) > 0:

        st.subheader("📋 Minhas comprovações")

        for comprovacao in reversed(
            dados["comprovacoes"]
        ):

            nome_arquivo = comprovacao["nome_arquivo"]
            status = comprovacao["status"]

            if status == "Pendente":

                st.warning(
                    "🟡 " +
                    nome_arquivo +
                    " — Pendente"
                )

            elif status == "Aprovado":

                st.success(
                    "🟢 " +
                    nome_arquivo +
                    " — Aprovado (+70 BIO)"
                )

            else:

                st.error(
                    "🔴 " +
                    nome_arquivo +
                    " — Reprovado"
                )


    # ========================================================
    # TRUST WALLET
    # ========================================================

    st.divider()

    st.header("👛 Minha Trust Wallet")

    st.caption(
        "A Trust Wallet é opcional. "
        "Você pode adicionar depois."
    )

    carteira = st.text_input(
        "Endereço público da Trust Wallet",
        value=dados["carteira"]
    )

    if st.button(
        "💾 Salvar carteira",
        use_container_width=True
    ):

        dados["carteira"] = carteira

        st.success(
            "Carteira salva!"
        )

        st.rerun()


    # ========================================================
    # CASHBACK
    # ========================================================

    st.divider()

    st.header("💵 Solicitar cashback")

    if bio >= LIMITE_BIO:

        if st.button(
            "💰 Solicitar R$50,00",
            use_container_width=True
        ):

            dados["cashback_solicitado"] = True

            st.success(
                "Solicitação enviada ao administrador."
            )

    else:

        st.info(
            "Você precisa chegar a 5.000 BIO "
            "para solicitar até R$50,00."
        )


    # ========================================================
    # PARCEIROS
    # ========================================================

    st.divider()

    st.header("🛍️ Parceiros")

    st.link_button(
        "🛒 Mercado Livre",
        "https://www.mercadolivre.com.br/social/sama6231844",
        use_container_width=True
    )

    st.link_button(
        "🏪 CoreStryke",
        "https://corestryke.com",
        use_container_width=True
    )


# ============================================================
# LOGIN / CADASTRO / ADMINISTRADOR
# ============================================================

else:

    login, cadastro, admin = st.tabs(
        [
            "🔐 Login",
            "📝 Cadastro",
            "🛡️ Administrador"
        ]
    )


    # ========================================================
    # LOGIN
    # ========================================================

    with login:

        st.header("🔐 Login")

        email_login = st.text_input(
            "E-mail",
            key="email_login"
        )

        senha_login = st.text_input(
            "Senha",
            type="password",
            key="senha_login"
        )

        if st.button(
            "🔓 Entrar",
            use_container_width=True
        ):

            email_login = email_login.strip().lower()

            if email_login == "":

                st.warning(
                    "Digite seu e-mail."
                )

            elif senha_login == "":

                st.warning(
                    "Digite sua senha."
                )

            elif email_login not in st.session_state.usuarios:

                st.error(
                    "E-mail não cadastrado."
                )

            else:

                usuario = st.session_state.usuarios[
                    email_login
                ]

                if senha_login != usuario["senha"]:

                    st.error(
                        "Senha incorreta."
                    )

                else:

                    st.session_state.usuario_logado = email_login

                    st.success(
                        "Login realizado!"
                    )

                    st.rerun()


    # ========================================================
    # CADASTRO
    # ========================================================

    with cadastro:

        st.header("📝 Criar conta")

        nome = st.text_input(
            "Nome completo",
            key="nome_cadastro"
        )

        email = st.text_input(
            "E-mail",
            key="email_cadastro"
        )

        senha = st.text_input(
            "Criar senha",
            type="password",
            key="senha_cadastro"
        )

        confirmar = st.text_input(
            "Confirmar senha",
            type="password",
            key="confirmar_cadastro"
        )

        carteira = st.text_input(
            "Trust Wallet (opcional)",
            key="carteira_cadastro",
            placeholder="Você pode adicionar depois"
        )

        if st.button(
            "📝 Criar minha conta",
            use_container_width=True
        ):

            nome = nome.strip()
            email = email.strip().lower()

            if nome == "":

                st.warning(
                    "Digite seu nome."
                )

            elif email == "":

                st.warning(
                    "Digite seu e-mail."
                )

            elif senha == "":

                st.warning(
                    "Crie uma senha."
                )

            elif senha != confirmar:

                st.error(
                    "As senhas não são iguais."
                )

            elif email in st.session_state.usuarios:

                st.error(
                    "Esse e-mail já está cadastrado."
                )

            else:

                st.session_state.usuarios[email] = {

                    "nome": nome,

                    "email": email,

                    "senha": senha,

                    "carteira": carteira,

                    "bio": 0,

                    "treinos": 0,

                    "treinos_lista": [],

                    "fotos": 0,

                    "comprovacoes": [],

                    "cashback_solicitado": False
                }

                st.success(
                    "🎉 Conta criada com sucesso!"
                )

                st.info(
                    "Agora vá para a aba Login e entre com seu e-mail e senha."
                )


    # ========================================================
    # ADMINISTRADOR
    # ========================================================

    with admin:

        st.header("🛡️ Administrador")

        senha_admin = st.text_input(
            "Senha do administrador",
            type="password",
            key="senha_admin"
        )

        if st.button(
            "🔓 Entrar como administrador",
            use_container_width=True
        ):

            if senha_admin == SENHA_ADMIN:

                st.session_state.admin_logado = True

                st.success(
                    "Administrador conectado."
                )

                st.rerun()

            else:

                st.error(
                    "Senha incorreta."
                )


# ============================================================
# PAINEL DO ADMINISTRADOR
# ============================================================

if st.session_state.admin_logado:

    st.divider()

    st.header("🛡️ Painel do Administrador")

    if st.button(
        "🚪 Sair do administrador",
        use_container_width=True
    ):

        st.session_state.admin_logado = False

        st.rerun()


    participantes = st.session_state.usuarios

    st.divider()

    st.subheader("📊 Resumo")

    total_participantes = len(participantes)

    total_bio = 0
    total_treinos = 0
    total_fotos = 0
    total_pendentes = 0

    for pessoa in participantes.values():

        total_bio += pessoa["bio"]

        total_treinos += pessoa["treinos"]

        total_fotos += len(
            pessoa["comprovacoes"]
        )

        for comprovacao in pessoa["comprovacoes"]:

            if comprovacao["status"] == "Pendente":

                total_pendentes += 1


    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "👥 Participantes",
            total_participantes
        )

    with col2:

        st.metric(
            "🪙 BIO distribuído",
            format(total_bio, ",")
        )


    col3, col4 = st.columns(2)

    with col3:

        st.metric(
            "🏋️ Treinos",
            total_treinos
        )

    with col4:

        st.metric(
            "🟡 Pendentes",
            total_pendentes
        )


    # ========================================================
    # PARTICIPANTES
    # ========================================================

    st.divider()

    st.subheader("👥 Participantes")

    if total_participantes == 0:

        st.info(
            "Nenhum participante cadastrado."
        )

    else:

        for email_pessoa in participantes:

            pessoa = participantes[email_pessoa]

            with st.expander(
                "👤 " + pessoa["nome"]
            ):

                st.write(
                    "📧 E-mail: " +
                    pessoa["email"]
                )

                st.write(
                    "🪙 BIO: " +
                    format(pessoa["bio"], ",")
                )

                st.write(
                    "🏋️ Treinos: " +
                    str(pessoa["treinos"])
                )

                st.write(
                    "📸 Comprovações: " +
                    str(len(pessoa["comprovacoes"]))
                )


                # --------------------------------------------
                # CARTEIRA
                # --------------------------------------------

                st.write(
                    "👛 Trust Wallet:"
                )

                if pessoa["carteira"] == "":

                    st.info(
                        "Carteira não cadastrada."
                    )

                else:

                    st.code(
                        pessoa["carteira"]
                    )


                # --------------------------------------------
                # TREINOS
                # --------------------------------------------

                st.write(
                    "### 🏋️ Histórico de treinos"
                )

                if len(pessoa["treinos_lista"]) == 0:

                    st.write(
                        "Nenhum treino registrado."
                    )

                else:

                    for treino in reversed(
                        pessoa["treinos_lista"]
                    ):

                        st.write(
                            "🏋️ " +
                            treino["atividade"]
                        )


                # --------------------------------------------
                # COMPROVAÇÕES
                # --------------------------------------------

                st.write(
                    "### 📸 Comprovações"
                )

                if len(pessoa["comprovacoes"]) == 0:

                    st.write(
                        "Nenhuma comprovação enviada."
                    )

                else:

                    for indice in range(
                        len(pessoa["comprovacoes"])
                    ):

                        comprovacao = pessoa[
                            "comprovacoes"
                        ][indice]

                        st.write(
                            "📄 " +
                            comprovacao["nome_arquivo"]
                        )

                        st.write(
                            "Status atual: " +
                            comprovacao["status"]
                        )


                        # -------------------------------
                        # PENDENTE
                        # -------------------------------

                        if comprovacao["status"] == "Pendente":

                            col_a, col_b = st.columns(2)

                            with col_a:

                                if st.button(
                                    "🟢 Aprovar",
                                    key="aprovar_" +
                                    email_pessoa +
                                    "_" +
                                    str(indice)
                                ):

                                    comprovacao["status"] = "Aprovado"

                                    if not comprovacao["bio_pago"]:

                                        pessoa["bio"] += BIO_FOTO

                                        comprovacao["bio_pago"] = True

                                    st.success(
                                        "Comprovação aprovada! +70 BIO."
                                    )

                                    st.rerun()


                            with col_b:

                                if st.button(
                                    "🔴 Reprovar",
                                    key="reprovar_" +
                                    email_pessoa +
                                    "_" +
                                    str(indice)
                                ):

                                    comprovacao["status"] = "Reprovado"

                                    st.warning(
                                        "Comprovação reprovada."
                                    )

                                    st.rerun()


                        elif comprovacao["status"] == "Aprovado":

                            st.success(
                                "🟢 Aprovado — +70 BIO já concedido."
                            )


                        else:

                            st.error(
                                "🔴 Reprovado — 0 BIO."
                            )


                # --------------------------------------------
                # CASHBACK
                # --------------------------------------------

                cashback = pessoa["bio"] * VALOR_BIO

                cashback = min(
                    cashback,
                    50
                )

                st.write(
                    "💰 Cashback: R$ " +
                    format(cashback, ".2f")
                )

                if pe
