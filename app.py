import streamlit as st

st.set_page_config(
    page_title="BioCore",
    page_icon="🧿",
    layout="centered"
)

LIMITE_BIO = 5000
VALOR_BIO = 0.01
BIO_TREINO = 10
BIO_FOTO = 70
SENHA_ADMIN = "1234"

MERCADO_LIVRE_LINK = "https://www.mercadolivre.com.br/social/sama6231844"
CORESTRYKE_LINK = "https://corestryke.com"


# =========================
# DADOS DA SESSÃO
# =========================

if "usuarios" not in st.session_state:
    st.session_state.usuarios = {}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if "admin_logado" not in st.session_state:
    st.session_state.admin_logado = False


# =========================
# TÍTULO
# =========================

st.title("🧬 BioCore")
st.caption("Treine, participe e acumule BIO.")


# ============================================================
# PARTICIPANTE
# ============================================================

if st.session_state.usuario_logado is not None:

    email_logado = st.session_state.usuario_logado
    pessoa = st.session_state.usuarios[email_logado]

    st.write("Olá, " + pessoa["nome"] + "! 👋")

    if st.button("🚪 Sair"):
        st.session_state.usuario_logado = None
        st.rerun()

    st.divider()

    # =========================
    # CASHBACK
    # =========================

    bio_atual = pessoa["bio"]

    cashback = min(
        bio_atual * VALOR_BIO,
        50
    )

    percentual = min(
        bio_atual / LIMITE_BIO * 100,
        100
    )

    st.subheader("💰 MEU CASHBACK")

    st.markdown(
        """
        <div style="
            padding:20px;
            border-radius:15px;
            border:1px solid #ddd;
            margin-bottom:15px;
        ">
        <h2>R$ {:.2f}</h2>

        <div style="
            background:#eeeeee;
            border-radius:10px;
            height:18px;
            width:100%;
        ">
            <div style="
                background:#21ba45;
                width:{:.1f}%;
                height:18px;
                border-radius:10px;
            "></div>
        </div>

        <p>{:.1f}%</p>
        <p><b>{:,} / {:,} BIO</b></p>

        </div>
        """.format(
            cashback,
            percentual,
            percentual,
            bio_atual,
            LIMITE_BIO
        ).replace(",", "."),
        unsafe_allow_html=True
    )

    bio_faltante = max(
        LIMITE_BIO - bio_atual,
        0
    )

    if bio_faltante > 0:
        st.write(
            "Faltam " +
            format(bio_faltante, ",").replace(",", ".") +
            " BIO para chegar a R$50,00."
        )
    else:
        st.write(
            "Você atingiu o limite de R$50,00 de cashback. 🎉"
        )

    st.divider()

    # =========================
    # TREINO
    # =========================

    st.subheader("🏋️ Treino / Atividade Física")

    st.write("O que você treinou hoje?")

    atividades = [
        "Peito, ombro e tríceps",
        "Costas e bíceps",
        "Quadríceps, glúteos e panturrilhas",
        "Perna completo",
        "Abdômen",
        "Peso corporal",
        "Corrida",
        "Futebol"
    ]

    atividade = st.selectbox(
        "Escolha uma atividade",
        atividades
    )

    if st.button("Registrar treino +10 BIO"):

        if "treinos_lista" not in pessoa:
            pessoa["treinos_lista"] = []

        pessoa["treinos_lista"].append(
            {
                "atividade": atividade,
                "status": "Registrado"
            }
        )

        pessoa["bio"] += BIO_TREINO

        st.success(
            "Treino registrado! +10 BIO 🧬"
        )

        st.rerun()

    st.write(
        "Total de treinos registrados: " +
        str(
            len(
                pessoa.get(
                    "treinos_lista",
                    []
                )
            )
        )
    )

    st.divider()

    # =========================
    # HISTÓRICO
    # =========================

    if len(pessoa.get("treinos_lista", [])) > 0:

        st.subheader("📋 Histórico de treinos")

        for numero, treino in enumerate(
            reversed(pessoa["treinos_lista"]),
            1
        ):

            st.write(
                str(numero) +
                ". " +
                treino["atividade"] +
                " — " +
                treino["status"]
            )

    st.divider()

    # =========================
    # FOTO SEMANAL
    # =========================

    st.subheader("📸 Foto semanal")

    st.write(
        "Envie uma foto comprovando sua atividade. "
        "A foto ficará pendente até a análise do administrador."
    )

    foto = st.file_uploader(
        "Enviar foto",
        type=["jpg", "jpeg", "png"],
        key="foto_participante"
    )

    if foto is not None:

        if st.button("Enviar foto para análise"):

            if "comprovacoes" not in pessoa:
                pessoa["comprovacoes"] = []

            pessoa["comprovacoes"].append(
                {
                    "nome_arquivo": foto.name,
                    "arquivo": foto.getvalue(),
                    "tipo": foto.type,
                    "status": "Pendente",
                    "bio_pago": False
                }
            )

            st.success(
                "Foto enviada! Aguarde a aprovação do administrador. 🟡"
            )

            st.rerun()

    # =========================
    # STATUS DAS FOTOS
    # =========================

    if len(pessoa.get("comprovacoes", [])) > 0:

        st.subheader("📷 Status das minhas fotos")

        for numero, comprovacao in enumerate(
            reversed(pessoa["comprovacoes"]),
            1
        ):

            status = comprovacao["status"]

            if status == "Pendente":
                icone = "🟡"

            elif status == "Aprovado":
                icone = "🟢"

            else:
                icone = "🔴"

            st.write(
                icone +
                " " +
                comprovacao["nome_arquivo"] +
                " — " +
                status
            )

            if status == "Aprovado":
                st.caption("+70 BIO")

            elif status == "Reprovado":
                st.caption("0 BIO")

    st.divider()

    # =========================
    # TRUST WALLET
    # =========================

    st.subheader("👛 Minha Trust Wallet")

    st.write(
        "A carteira é opcional. Você pode cadastrar agora "
        "ou adicionar depois."
    )

    carteira_atual = st.text_input(
        "Endereço da Trust Wallet",
        value=pessoa.get("wallet", ""),
        placeholder="0x..."
    )

    if st.button("Salvar carteira"):

        pessoa["wallet"] = carteira_atual.strip()

        st.success(
            "Carteira salva com sucesso."
        )

        st.rerun()

    st.divider()

    # =========================
    # CASHBACK
    # =========================

    st.subheader("💵 Solicitar cashback")

    if bio_atual >= LIMITE_BIO:

        st.write(
            "Cashback disponível: R$50,00"
        )

        if pessoa.get(
            "cashback_solicitado",
            False
        ):

            if pessoa.get(
                "cashback_pago",
                False
            ):

                st.success(
                    "Cashback marcado como pago pelo administrador. ✅"
                )

            else:

                st.info(
                    "Seu cashback já foi solicitado e está aguardando pagamento."
                )

        else:

            if st.button(
                "Solicitar cashback de R$50,00"
            ):

                pessoa["cashback_solicitado"] = True
                pessoa["cashback_pago"] = False

                st.success(
                    "Solicitação enviada para análise do BioCore."
                )

                st.rerun()

    else:

        st.info(
            "Você precisa acumular 5.000 BIO para solicitar "
            "o cashback máximo de R$50,00."
        )

    st.divider()

    # =========================
    # MERCADO LIVRE
    # =========================

    st.subheader("🛒 Mercado Livre")

    st.write(
        "Faça suas compras pelo link de afiliado BioCore."
    )

    st.link_button(
        "🛒 Comprar no Mercado Livre",
        MERCADO_LIVRE_LINK
    )

    st.write(
        "25% da comissão gerada pela compra é destinada "
        "ao participante em BIO."
    )

    st.divider()

    # =========================
    # CORESTRYKE
    # =========================

    st.subheader("🏪 CoreStryke")

    st.write(
        "Os BIO acumulados podem ser utilizados para obter "
        "descontos nas compras da CoreStryke."
    )

    st.write(
        "O desconto é calculado de acordo com a quantidade "
        "de BIO disponível, conforme a tabela de conversão do BioCore."
    )

    st.write(
        "Os BIO utilizados em uma compra são descontados "
        "do saldo do participante."
    )

    st.write(
        "BIO utilizado em desconto na CoreStryke deixa de "
        "contar para o cashback."
    )

    st.write(
        "O mesmo BIO não pode ser utilizado duas vezes: "
        "ou é usado como desconto na CoreStryke, ou permanece "
        "disponível para o cashback."
    )

    st.link_button(
        "🏪 Acessar CoreStryke",
        CORESTRYKE_LINK
    )

    st.divider()

    # =========================
    # REGRAS
    # =========================

    st.subheader("📜 Regras do BioCore")

    st.markdown(
        """
### 🏋️ Treinos e atividades

- Cada treino/atividade física registrado vale **+10 BIO**.
- Deve ser registrado um treino por vez.

### 📸 Foto semanal

- Envie uma foto comprovando sua atividade.
- A foto fica **Pendente** até a análise do administrador.
- Foto **Aprovada**: +70 BIO.
- Foto **Reprovada**: 0 BIO.
- Limite de **1 foto por semana**.

### 🛒 Mercado Livre

- Faça suas compras através do link de afiliado BioCore.
- **25% da comissão gerada pela compra é revertida ao participante em BIO**.
- O valor recebido depende da comissão efetivamente gerada pela compra.

### 🏪 CoreStryke

- Os BIO acumulados podem ser utilizados para obter descontos nas compras da CoreStryke.
- Os BIO utilizados em uma compra são descontados do saldo do participante.
- BIO utilizado em desconto na CoreStryke deixa de contar para o cashback.

### 💰 Cashback

- **1 BIO = R$ 0,01** para fins de cálculo do cashback.
- O limite para conversão é de **5.000 BIO = R$ 50,00**.
- O cashback está sujeito à análise e aprovação do BioCore.
"""
    )


# ============================================================
# LOGIN / CADASTRO / ADMIN
# ============================================================

else:

    aba_login, aba_cadastro, aba_admin = st.tabs(
        [
            "🔐 Login",
            "📝 Cadastro",
            "🛡️ Administrador"
        ]
    )

    # =========================
    # LOGIN
    # =========================

    with aba_login:

        st.subheader("🔐 Login")

        email_login = st.text_input(
            "E-mail",
            key="login_email"
        )

        senha_login = st.text_input(
            "Senha",
            type="password",
            key="login_senha"
        )

        if st.button(
            "Entrar",
            key="botao_login"
        ):

            email_login = email_login.strip().lower()

            if email_login in st.session_state.usuarios:

                pessoa = st.session_state.usuarios[email_login]

                if pessoa["senha"] == senha_login:

                    st.session_state.usuario_logado = email_login

                    st.success(
                        "Login realizado com sucesso!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Senha incorreta."
                    )

            else:

                st.error(
                    "E-mail não cadastrado."
                )

    # =========================
    # CADASTRO
    # =========================

    with aba_cadastro:

        st.subheader("📝 Cadastro")

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

        confirmar_senha = st.text_input(
            "Confirmar senha",
            type="password",
            key="confirmar_senha"
        )

        wallet = st.text_input(
            "Trust Wallet (opcional)",
            placeholder="0x..."
        )

        if st.button(
            "Criar cadastro",
            key="botao_cadastro"
        ):

            email_novo = email.strip().lower()

            if nome.strip() == "":
                st.error("Digite seu nome.")

            elif email_novo == "":
                st.error("Digite seu e-mail.")

            elif senha == "":
                st.error("Digite uma senha.")

            elif senha != confirmar_senha:
                st.error("As senhas não são iguais.")

            elif email_novo in st.session_state.usuarios:
                st.error("Este e-mail já está cadastrado.")

            else:

                st.session_state.usuarios[email_novo] = {
                    "nome": nome.strip(),
                    "email": email_novo,
                    "senha": senha,
                    "wallet": wallet.strip(),
                    "bio": 0,
                    "treinos_lista": [],
                    "comprovacoes": [],
                    "cashback_solicitado": False,
                    "cashback_pago": False
                }

                st.success(
                    "Cadastro realizado com sucesso! "
                    "Agora você pode entrar pela aba Login."
                )

    # =========================
    # ADMINISTRADOR
    # =========================

    with aba_admin:

        st.subheader("🛡️ Administrador")

        senha_admin = st.text_input(
            "Senha do administrador",
            type="password",
            key="senha_admin"
        )

        if st.button(
            "Entrar como administrador",
            key="botao_admin"
        ):

            if senha_admin == SENHA_ADMIN:

                st.session_state.admin_logado = True

                st.success(
                    "Acesso administrativo liberado."
                )

                st.rerun()

            else:

                st.error(
                    "Senha de administrador incorreta."
                )


# ============================================================
# PAINEL ADMINISTRATIVO
# ============================================================

if st.session_state.admin_logado:

    st.divider()

    st.header("🛡️ Painel Administrativo")

    if st.button(
        "🚪 Sair do administrador",
        key="sair_admin"
    ):

        st.session_state.admin_logado = False
        st.rerun()

    usuarios = st.session_state.usuarios

    st.write(
        "Total de participantes: " +
        str(len(usuarios))
    )

    st.divider()

    if len(usuarios) == 0:

        st.info(
            "Ainda não existem participantes cadastrados."
        )

    else:

        for email_participante, pessoa in usuarios.items():

            st.subheader(
                "👤 " +
                pessoa["nome"]
            )

            st.write(
                "📧 E-mail: " +
                pessoa["email"]
            )

            st.write(
                "🧬 BIO: " +
                str(pessoa["bio"])
            )

            st.write(
                "🏋️ Treinos registrados: " +
                str(
                    len(
                        pessoa.get(
                            "treinos_lista",
                            []
                        )
                    )
                )
            )

            st.write(
                "📸 Comprovações: " +
                str(
                    len(
                        pessoa.get(
                            "comprovacoes",
                            []
                        )
                    )
                )
            )

            wallet_admin = pessoa.get(
                "wallet",
                ""
            )

            if wallet_admin:

                st.write(
                    "👛 Trust Wallet: " +
                    wallet_admin
                )

            else:

                st.write(
                    "👛 Trust Wallet: não cadastrada"
                )

            cashback_admin = min(
                pessoa["bio"] * VALOR_BIO,
                50
            )

            st.write(
                "💰 Cashback calculado: R$ " +
                format(
                    cashback_admin,
                    ".2f"
                )
            )

            # =========================
            # HISTÓRICO
            # =========================

            with st.expander(
                "🏋️ Ver histórico de treinos"
            ):

                treinos_admin = pessoa.get(
                    "treinos_lista",
                    []
                )

                if len(treinos_admin) == 0:

                    st.write(
                        "Nenhum treino registrado."
                    )

                else:

                    for treino in treinos_admin:

                        st.write(
                            "• " +
                            treino["atividade"] +
                            " — " +
                            treino["status"]
                        )

            # =========================
            # COMPROVAÇÕES
            # =========================

            with st.expander(
                "📸 Ver fotos e aprovar/reprovar"
            ):

                comprovacoes_admin = pessoa.get(
                    "comprovacoes",
                    []
                )

                if len(comprovacoes_admin) == 0:

                    st.write(
                        "Nenhuma foto enviada."
                    )

                else:

                    for indice, comprovacao in enumerate(
                        comprovacoes_admin
                    ):

                        st.write(
                            "📷 " +
                            comprovacao["nome_arquivo"]
                        )

                        st.write(
                            "Status: " +
                            comprovacao["status"]
                        )

                        # =========================
                        # MOSTRAR FOTO
                        # =========================

                        if "arquivo" in comprovacao:

                            st.image(
                                comprovacao["arquivo"],
                                caption=comprovacao["nome_arquivo"],
                                width=300
                            )

                        # =========================
                        # APROVAR / REPROVAR
                        # =========================

                        if comprovacao["status"] == "Pendente":

                            coluna1, coluna2 = st.columns(2)

                            with coluna1:

                                if st.button(
                                    "🟢 Aprovar",
                                    key="aprovar_" + email_participante + "_" + str(indice)
                                ):

                                    comprovacao["status"] = "Aprovado"

                                    if not comprovacao.get(
                                        "bio_pago",
                                        False
                                    ):

                                        pessoa["bio"] += B
