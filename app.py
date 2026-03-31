import streamlit as st
import hashlib
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

# ---------------- CÓDIGOS DE CONVITE ----------------
CODIGOS_VALIDOS = {
    "PROF123": "Professor",
    "TESTE1": "Teste",
    "AMIGO1": "Amigo"
}

ADMIN_USER = "Guilherme Ferreira"

# ---------------- BANCO ----------------
conn = sqlite3.connect("estoque.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa TEXT,
    usuario TEXT,
    senha TEXT
)
""")
conn.commit()

# ---------------- HASH ----------------
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ---------------- SESSION ----------------
for key in ['logado', 'empresa', 'usuario', 'login_user', 'login_senha']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'logado' else ""

# ---------------- LOGIN ----------------
def login_usuario():
    user = st.session_state["login_user"].strip()
    password = st.session_state["login_senha"].strip()

    if not user or not password:
        st.warning("Preencha usuário e senha")
        return

    password_hash = hash_senha(password)

    cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (user,))
    usuario_existente = cursor.fetchone()

    if usuario_existente and usuario_existente[3] == password_hash:
        st.session_state['logado'] = True
        st.session_state['empresa'] = usuario_existente[1]
        st.session_state['usuario'] = usuario_existente[2]
        st.rerun()
    else:
        st.error("❌ Usuário ou senha inválidos")

# ---------------- LOGOUT ----------------
def logout_usuario():
    st.session_state['logado'] = False
    st.session_state['empresa'] = ""
    st.session_state['usuario'] = ""
    st.rerun()

# ---------------- LOGIN SCREEN ----------------
if not st.session_state['logado']:

    st.title("🚀 StockMind IA")
    st.markdown("### Gestão inteligente de estoque com IA")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Criar conta")
        empresa = st.text_input("Empresa")
        novo_user = st.text_input("Usuário")
        nova_senha = st.text_input("Senha", type="password")
        codigo_convite = st.text_input("Código de convite")

        if st.button("Cadastrar"):
            if codigo_convite not in CODIGOS_VALIDOS and novo_user != ADMIN_USER:
                st.error("❌ Código inválido")
            elif empresa and novo_user and nova_senha:
                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa, novo_user, hash_senha(nova_senha))
                )
                conn.commit()
                st.success("✅ Conta criada!")
            else:
                st.warning("Preencha todos os campos")

    with col2:
        st.subheader("🔐 Login")
        st.text_input("Usuário", key="login_user")
        st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            login_usuario()

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("📊 StockMind IA")
st.sidebar.success(f"Empresa: {st.session_state['empresa']}")

if st.sidebar.button("🚪 Sair"):
    logout_usuario()

# ADMIN RESET
if st.session_state['usuario'] == ADMIN_USER:
    if st.sidebar.button("⚠️ Resetar usuários"):
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        st.success("Reset realizado")

# ---------------- MENU (AGORA FIXO) ----------------
pagina = st.sidebar.radio("Menu", [
    "🏠 Visão Geral",
    "📦 Produtos",
    "💰 Financeiro",
    "🤖 IA"
])

# ---------------- UPLOAD ----------------
file = st.sidebar.file_uploader("Upload", type=["csv", "xlsx"])

df = None

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df.columns = df.columns.str.strip()

# ---------------- TELAS ----------------

if pagina == "🏠 Visão Geral":

    st.title("📊 Dashboard")

    if df is None:
        st.info("👈 Envie uma planilha para visualizar os dados")
    else:
        total = (df["Estoque Atual"] * 50).sum()
        st.metric("Estoque Total", f"R$ {total:,.2f}")

elif pagina == "📦 Produtos":

    st.title("📦 Produtos")

    if df is None:
        st.info("Envie a planilha")
    else:
        produto = st.selectbox("Produto", df["Produto"].unique())
        st.dataframe(df[df["Produto"] == produto])

elif pagina == "💰 Financeiro":

    st.title("💰 Financeiro")

    if df is None:
        st.info("Envie a planilha")
    else:
        total = df["Estoque Atual"].sum()
        st.metric("Total", total)

elif pagina == "🤖 IA":

    st.title("🤖 IA")

    if df is None:
        st.info("Envie a planilha")
    else:
        produto = st.selectbox("Produto", df["Produto"].unique())
        vendas = df[df["Produto"] == produto][['Venda Mês 1','Venda Mês 2','Venda Mês 3']].values.flatten()

        X = np.array(range(len(vendas))).reshape(-1, 1)
        modelo = LinearRegression().fit(X, vendas)
        previsao = modelo.predict([[len(vendas)]])[0]

        st.metric("Previsão", round(previsao))
