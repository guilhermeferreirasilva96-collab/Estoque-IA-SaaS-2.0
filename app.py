import streamlit as st
import hashlib
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

# ---------------- CONFIG ----------------
st.set_page_config(page_title="StockMind IA", layout="wide")

# ---------------- CÓDIGOS ----------------
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

# ---------------- FORMATAÇÃO REAL ----------------
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

if st.session_state['usuario'] == ADMIN_USER:
    if st.sidebar.button("⚠️ Resetar usuários"):
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        st.success("Reset realizado")

pagina = st.sidebar.radio("Menu", [
    "🏠 Visão Geral",
    "📦 Produtos",
    "💰 Financeiro",
    "🤖 IA"
])

file = st.sidebar.file_uploader("Upload", type=["csv", "xlsx"])

df = None

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df['Produto'] = df['Produto'].astype(str).str.strip()

    if "Símbolo" in df.columns:
        df["Símbolo"] = df["Símbolo"].astype(str).str.strip()

    if "Valor Unitário" in df.columns:
        df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")
        df["Valor Estoque"] = df["Estoque Atual"] * df["Valor Unitário"]
    else:
        df["Valor Estoque"] = df["Estoque Atual"] * 50

# ================= VISÃO GERAL =================
if pagina == "🏠 Visão Geral":

    st.title("📊 Dashboard Inteligente")

    if df is None or df.empty:
        st.info("👈 Envie uma planilha")
    else:
        total = df["Valor Estoque"].sum()
        economia = total * 0.2
        giro_medio = df["Estoque Atual"].mean()

        ruptura = len(df[df["Estoque Atual"] < giro_medio])
        excesso = len(df[df["Estoque Atual"] > giro_medio * 1.5])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Estoque Total", formatar_real(total))
        col2.metric("📉 Economia Potencial", formatar_real(economia))
        col3.metric("⚠️ Ruptura", ruptura)
        col4.metric("📦 Excesso", excesso)

        resumo = df.groupby("Produto").agg({
            "Estoque Atual": "sum",
            "Valor Estoque": "sum"
        }).reset_index()

        st.subheader("📊 Estoque por Produto")
        fig1, ax1 = plt.subplots()
        ax1.bar(resumo["Produto"], resumo["Estoque Atual"])
        st.pyplot(fig1)

        st.subheader("💰 Valor por Produto")
        fig2, ax2 = plt.subplots()
        ax2.bar(resumo["Produto"], resumo["Valor Estoque"])
        st.pyplot(fig2)

# ================= PRODUTOS =================
elif pagina == "📦 Produtos":

    st.title("📦 Análise de Produtos")

    if df is None:
        st.info("Envie a planilha")
    else:
        produto = st.selectbox("Produto", df["Produto"].unique())
        df_filtrado = df[df["Produto"] == produto]

        st.dataframe(df_filtrado)

        unidade = df_filtrado["Símbolo"].iloc[0] if "Símbolo" in df.columns else "un"

        vendas = df_filtrado[['Venda Mês 1','Venda Mês 2','Venda Mês 3']].values.flatten()

        st.subheader("📈 Histórico de Vendas")
        fig, ax = plt.subplots()
        ax.plot(vendas, marker='o')
        st.pyplot(fig)

        st.subheader("📊 Estoque vs Média")
        estoque = df_filtrado["Estoque Atual"].values[0]
        media = np.mean(vendas)

        fig2, ax2 = plt.subplots()
        ax2.bar(["Estoque", "Média"], [estoque, media])
        st.pyplot(fig2)

# ================= FINANCEIRO =================
elif pagina == "💰 Financeiro":

    st.title("💰 Financeiro")

    if df is None:
        st.info("Envie a planilha")
    else:
        resumo = df.groupby("Produto")["Valor Estoque"].sum().reset_index()

        resumo_formatado = resumo.copy()
        resumo_formatado["Valor Estoque"] = resumo_formatado["Valor Estoque"].apply(formatar_real)

        st.dataframe(resumo_formatado)

        fig, ax = plt.subplots()
        ax.bar(resumo["Produto"], resumo["Valor Estoque"])
        st.pyplot(fig)

# ================= IA =================
elif pagina == "🤖 IA":

    st.title("🤖 Previsão com IA")

    if df is None:
        st.info("Envie a planilha")
    else:
        produto = st.selectbox("Produto", df["Produto"].unique())

        df_filtrado = df[df["Produto"] == produto]
        vendas = df_filtrado[['Venda Mês 1','Venda Mês 2','Venda Mês 3']].values.flatten()

        unidade = df_filtrado["Símbolo"].iloc[0] if "Símbolo" in df.columns else "un"

        X = np.array(range(len(vendas))).reshape(-1, 1)
        modelo = LinearRegression().fit(X, vendas)
        previsao = modelo.predict([[len(vendas)]])[0]

        media = np.mean(vendas)

        col1, col2 = st.columns(2)
        col1.metric("📈 Previsão IA", f"{round(previsao)} {unidade}")
        col2.metric("📊 Média", f"{round(media)} {unidade}")

        fig, ax = plt.subplots()
        ax.plot(vendas, marker='o', label="Histórico")
        ax.axhline(previsao, linestyle='--', label="Previsão IA")
        ax.legend()

        st.pyplot(fig)
        st.caption("Linha contínua: histórico | Linha tracejada: previsão da IA")
