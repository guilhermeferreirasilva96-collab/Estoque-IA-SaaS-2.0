import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
import sqlite3
import hashlib

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

# ---------------- HASH SENHA ----------------
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ---------------- SESSION ----------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if "empresa" not in st.session_state:
    st.session_state.empresa = ""

# ---------------- FUNÇÃO MOEDA ----------------
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------------- LOGIN / CADASTRO ----------------
if not st.session_state.logado:

    st.markdown("""
        <style>
        .block-container {
            max-width: 900px;
            margin: auto;
            padding-top: 80px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚀 StockMind IA")
    st.markdown("### Gestão inteligente de estoque com IA")

    col1, col2 = st.columns(2)

    # -------- CADASTRO --------
    with col1:
        st.subheader("📝 Criar conta")

        empresa = st.text_input("Empresa", key="cad_empresa")
        novo_user = st.text_input("Usuário", key="cad_user")
        nova_senha = st.text_input("Senha", type="password", key="cad_senha")
        codigo_convite = st.text_input("Código de convite", type="password")

        if st.button("Cadastrar"):
            if codigo_convite not in CODIGOS_VALIDOS:
                st.error("❌ Código de convite inválido")

            elif empresa and novo_user and nova_senha:
                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa.strip(), novo_user.strip(), hash_senha(nova_senha.strip()))
                )
                conn.commit()

                st.success("✅ Conta criada com sucesso!")
            else:
                st.warning("Preencha todos os campos")

    # -------- LOGIN --------
    with col2:
        st.subheader("🔐 Login")

        user = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            cursor.execute(
                "SELECT * FROM usuarios WHERE TRIM(usuario)=? AND senha=?",
                (user.strip(), hash_senha(password.strip()))
            )
            result = cursor.fetchone()

            if result:
                st.session_state.logado = True
                st.session_state.empresa = result[1]
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    st.markdown("---")
    st.caption("© 2026 StockMind IA")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("StockMind IA")

if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.session_state.empresa = ""
    st.rerun()

pagina = st.sidebar.radio(
    "Menu",
    ["🏠 Visão Geral", "📦 Produtos", "💰 Financeiro", "🤖 IA"]
)

st.title("🚀 StockMind IA")

# ---------------- UPLOAD ----------------
file = st.sidebar.file_uploader("Upload", type=["xlsx", "csv"])

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

    df.columns = df.columns.str.strip()
    df['Produto'] = df['Produto'].astype(str).str.strip()

    if "Valor Unitário" in df.columns:
        df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")
        df["Valor Estoque"] = df["Estoque Atual"] * df["Valor Unitário"]
    else:
        df["Valor Estoque"] = df["Estoque Atual"] * 50

    if pagina == "🏠 Visão Geral":
        st.subheader("Dashboard")

        total = df["Valor Estoque"].sum()
        st.metric("💰 Total", formatar_real(total))

    elif pagina == "📦 Produtos":
        produto = st.selectbox("Produto", df["Produto"].unique())
        st.dataframe(df[df["Produto"] == produto])

    elif pagina == "💰 Financeiro":
        total = df["Valor Estoque"].sum()
        st.metric("💰 Total", formatar_real(total))

    elif pagina == "🤖 IA":
        produto = st.selectbox("Produto", df["Produto"].unique())
        df_filtrado = df[df["Produto"] == produto]

        vendas = df_filtrado[['Venda Mês 1', 'Venda Mês 2', 'Venda Mês 3']].values.flatten()

        X = np.array(range(len(vendas))).reshape(-1, 1)
        modelo = LinearRegression().fit(X, vendas)

        previsao = round(modelo.predict([[len(vendas)]])[0])

        st.metric("📈 Previsão", previsao)

else:
    st.info("Envie uma planilha")
