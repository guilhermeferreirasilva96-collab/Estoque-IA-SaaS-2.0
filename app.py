import streamlit as st
import hashlib
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

# ---------------- CONFIG ----------------
st.set_page_config(page_title="StockMind IA", layout="wide")

# ---------------- CÓDIGOS DE CONVITE ----------------
CODIGOS_VALIDOS = {
    "PROF123": "Professor",
    "TESTE1": "Teste",
    "AMIGO1": "Amigo"
}

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
for key in ['logado', 'empresa', 'usuario']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'logado' else ""

# ---------------- LOGIN ----------------
def login_usuario(user, password):
    user_clean = user.strip()
    password_hash = hash_senha(password.strip())

    cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (user_clean,))
    usuario = cursor.fetchone()

    if usuario and usuario[3] == password_hash:
        st.session_state['logado'] = True
        st.session_state['empresa'] = usuario[1]
        st.session_state['usuario'] = usuario[2]
        return True
    else:
        return False

# ---------------- LOGOUT ----------------
def logout_usuario():
    st.session_state['logado'] = False
    st.session_state['empresa'] = ""
    st.session_state['usuario'] = ""

# ---------------- LOGIN / CADASTRO ----------------
if not st.session_state['logado']:

    st.markdown("""
        <style>
        .block-container { max-width: 900px; margin: auto; padding-top: 80px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚀 StockMind IA")
    st.markdown("### Gestão inteligente de estoque com IA")

    col1, col2 = st.columns(2)

    # CADASTRO
    with col1:
        st.subheader("📝 Criar conta")
        empresa = st.text_input("Empresa")
        novo_user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        codigo = st.text_input("Código de convite", type="password")

        if st.button("Cadastrar"):
            if codigo not in CODIGOS_VALIDOS and novo_user != "Guilherme Ferreira":
                st.error("❌ Código inválido")
            elif empresa and novo_user and senha:
                tipo = CODIGOS_VALIDOS[codigo] if codigo in CODIGOS_VALIDOS else "Admin"

                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa.strip(), novo_user.strip(), hash_senha(senha.strip()))
                )
                conn.commit()

                if codigo in CODIGOS_VALIDOS:
                    del CODIGOS_VALIDOS[codigo]

                st.success(f"✅ Conta criada! Tipo: {tipo}")
            else:
                st.warning("Preencha todos os campos")

    # LOGIN
    with col2:
        st.subheader("🔐 Login")
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if login_usuario(user, password):
                st.success(f"Bem-vindo {user}")
                st.stop()
            else:
                st.error("❌ Usuário ou senha inválidos")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## StockMind IA")

if st.session_state['empresa']:
    st.sidebar.success(f"Empresa: {st.session_state['empresa']}")

# RESET ADMIN
if st.session_state['usuario'] == "Guilherme Ferreira":
    if st.sidebar.button("⚠️ Resetar usuários"):
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        st.success("Reset realizado")

# LOGOUT
if st.sidebar.button("🚪 Sair"):
    logout_usuario()
    st.stop()

# ---------------- UPLOAD ----------------
file = st.sidebar.file_uploader("📁 Upload da planilha", type=["xlsx", "csv"])

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df['Produto'] = df['Produto'].astype(str).str.strip()

    if "Valor Unitário" in df.columns:
        df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")
        df["Valor Estoque"] = df["Estoque Atual"] * df["Valor Unitário"]
    else:
        df["Valor Estoque"] = df["Estoque Atual"] * 50

    pagina = st.sidebar.radio("Menu", ["🏠 Visão Geral", "📦 Produtos", "💰 Financeiro", "🤖 IA"])

    # VISÃO GERAL
    if pagina == "🏠 Visão Geral":
        st.subheader("📊 Dashboard")
        total = df["Valor Estoque"].sum()
        st.metric("💰 Estoque Total", f"R$ {total:,.2f}")

    # PRODUTOS
    elif pagina == "📦 Produtos":
        produto = st.selectbox("Produto", df["Produto"].unique())
        st.dataframe(df[df["Produto"] == produto])

    # FINANCEIRO
    elif pagina == "💰 Financeiro":
        total = df["Valor Estoque"].sum()
        economia = total * 0.2
        st.metric("💰 Total", f"R$ {total:,.2f}")
        st.metric("📉 Economia", f"R$ {economia:,.2f}")

    # IA
    elif pagina == "🤖 IA":
        produto = st.selectbox("Produto", df["Produto"].unique())
        df_filtrado = df[df["Produto"] == produto]

        vendas = df_filtrado[['Venda Mês 1','Venda Mês 2','Venda Mês 3']].values.flatten()
        X = np.arange(len(vendas)).reshape(-1,1)
        modelo = LinearRegression().fit(X, vendas)

        previsao = modelo.predict([[len(vendas)]])[0]

        st.metric("📈 Previsão IA", round(previsao))

else:
    st.info("👈 Envie a planilha para começar")
