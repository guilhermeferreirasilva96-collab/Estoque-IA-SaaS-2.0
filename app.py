import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
import sqlite3

st.set_page_config(page_title="StockMind IA", layout="wide")

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

# ---------------- FUNÇÃO MOEDA ----------------
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------------- LOGIN STATE ----------------
if "logado" not in st.session_state:
    st.session_state.logado = False

# ---------------- LOGIN UI ----------------
def login():
    st.markdown("""
        <style>
        .block-container {
            max-width: 400px;
            margin: auto;
            padding-top: 100px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🔐 StockMind IA")
    st.markdown("### Login")

    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND senha=?",
            (user, password)
        )
        result = cursor.fetchone()

        if result:
            st.session_state.logado = True
            st.session_state.empresa = result[1]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

# 👉 Se não estiver logado → só mostra login
if not st.session_state.logado:
    login()
    st.stop()

# ---------------- SIDEBAR (SÓ APÓS LOGIN) ----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
st.sidebar.markdown("## StockMind IA")
st.sidebar.caption("Gestão inteligente de estoque")

st.sidebar.success(f"Empresa: {st.session_state.empresa}")

# Logout
if st.sidebar.button("🚪 Sair"):
    st.session_state.logado = False
    st.rerun()

# Menu
pagina = st.sidebar.radio(
    "Menu",
    ["🏠 Visão Geral", "📦 Produtos", "💰 Financeiro", "🤖 IA"]
)

# ---------------- HEADER ----------------
st.title("🚀 StockMind IA")
st.markdown("### Transforme seu estoque em dinheiro com inteligência artificial")

# ---------------- UPLOAD ----------------
file = st.sidebar.file_uploader("📁 Upload da planilha", type=["xlsx", "csv"])

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df['Produto'] = df['Produto'].astype(str).str.strip()

    valor_unitario = 50.0
    df["Valor Estoque"] = df["Estoque Atual"] * valor_unitario

    # ================= VISÃO GERAL =================
    if pagina == "🏠 Visão Geral":

        st.subheader("📊 Dashboard Executivo")

        total = df["Valor Estoque"].sum()
        economia = total * 0.2

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Estoque Total", formatar_real(total))
        col2.metric("📉 Economia Potencial", formatar_real(economia))
        col3.metric("📦 Produtos", len(df))

        fig, ax = plt.subplots()
        ax.bar(["Atual", "Otimizado"], [total, total * 0.8])
        st.pyplot(fig)

    # ================= PRODUTOS =================
    elif pagina == "📦 Produtos":

        st.subheader("📦 Análise de Produtos")

        produto = st.selectbox("Produto", df["Produto"].unique())
        st.dataframe(df[df["Produto"] == produto])

    # ================= FINANCEIRO =================
    elif pagina == "💰 Financeiro":

        st.subheader("💰 Financeiro")

        valor_unitario = st.number_input("Valor unitário (R$)", value=50.0)
        df["Valor Estoque"] = df["Estoque Atual"] * valor_unitario

        total = df["Valor Estoque"].sum()
        economia = total * 0.2

        col1, col2 = st.columns(2)
        col1.metric("💰 Estoque Total", formatar_real(total))
        col2.metric("📉 Economia", formatar_real(economia))

        fig, ax = plt.subplots()
        ax.pie([total * 0.8, economia], labels=["Otimizado", "Economia"], autopct='%1.1f%%')
        st.pyplot(fig)

    # ================= IA =================
    elif pagina == "🤖 IA":

        st.subheader("🤖 Inteligência Artificial")

        produto = st.selectbox("Produto", df["Produto"].unique())
        df_filtrado = df[df["Produto"] == produto]

        vendas = df_filtrado[['Venda Mês 1', 'Venda Mês 2', 'Venda Mês 3']].values.flatten()

        X = np.array(range(len(vendas))).reshape(-1, 1)
        modelo = LinearRegression().fit(X, vendas)

        previsao = modelo.predict([[len(vendas)]])[0]

        st.metric("📈 Previsão", int(previsao))

        fig, ax = plt.subplots()
        ax.plot(vendas, marker='o')
        ax.axhline(previsao, linestyle='--')
        st.pyplot(fig)

else:
    st.info("👈 Envie a planilha para começar")
