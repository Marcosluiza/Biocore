import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date

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

BATTLE_WITHIN = (
    "https://drive.google.com/uc?export=download"
    "&id=1VoOv0AacWqtweJBlmXd6awJe-bOdmfRX"
)

BIO_TREINO = 10
BIO_FOTO = 70
MINIMO_SAQUE = 5000
MINIMO_COMPRAS = 2


# =========================================================
# BANCO DE DADOS
# =========================================================

def conectar():
    return sqlite3.connect(DB)


def criar_banco():
    conn = conectar()
    c = conn.cursor()

    # Participantes
    c.execute("""
        CREATE TABLE IF NOT EXISTS participantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            bio INTEGER DEFAULT 0,
            compras_qualificadas INTEGER DEFAULT 0
        )
    """)

    # Treinos
    c.execute("""
        CREATE TABLE IF NOT EXISTS treinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            atividade TEXT NOT NULL,
            data TEXT NOT NULL,
            bio INTEGER DEFAULT 10
        )
    """)

    # Fotos
    c.execute("""
        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            semana TEXT NOT NULL,
            arquivo TEXT NOT NULL,
            bio INTEGER DEFAULT 70
        )
    """)

    # Fases do jogo
    c.execute("""
        CREATE TABLE IF NOT EXISTS fases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            fase INTEGER NOT NULL,
            bio INTEGER NOT NULL,
            UNIQUE(participante_id, fase)
        )
    """)

    # Compras
    c.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participante_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            comissao REAL DEFAULT 0,
            bio INTEGER DEFAULT 0,
            validada INTEGER DEFAULT 0,
            data TEXT NOT NULL
        )
    """)

    # Saques
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
# FUNÇÕES
# =========================================================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def criar_conta(nome, email, senha):
    conn = conectar()
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO participantes
            (nome, email, senha, bio, compras_qualificadas)
            VALUES (?, ?, ?, 0, 0)
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


def obter_participante(participante_id):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        SELECT id, nome, email, bio, compras_qualificadas
        FROM participantes
        WHERE id = ?
    """, (participante_id,))

    resultado = c.fetchone()
    conn.close()

    return resultado


def adicionar_bio(participante_id, quantidade):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
        UPDATE participantes
        SET bio = bio + ?
        WHERE id = ?
    """, (quantidade, participante_id))

    conn.commit()
    conn.close()


def
