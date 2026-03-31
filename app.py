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

    if "Valor Unitário" in df.columns:
        df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")
        df["Valor Estoque"] = df["Estoque Atual"] * df["Valor Unitário"]
    else:
        df["Valor Estoque"] = df["Estoque Atual"] * 50

# ================= VISÃO GERAL =================
if pagina == "🏠 Visão Geral":

    st.title("📊 Dashboard Inteligente")

    if df is None:
        st.info("👈 Envie uma planilha")
    else:
        total = df["Valor Estoque"].sum()
        economia = total * 0.2
        giro_medio = df["Estoque Atual"].mean()

        ruptura = len(df[df["Estoque Atual"] < giro_medio])
        excesso = len(df[df["Estoque Atual"] > giro_medio * 1.5])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Estoque Total", f"R$ {total:,.2f}")
        col2.metric("📉 Economia Potencial", f"R$ {economia:,.2f}")
        col3.metric("⚠️ Ruptura", ruptura)
        col4.metric("📦 Excesso", excesso)

        st.subheader("🤖 Alertas Inteligentes")

        for _, row in df.iterrows():
            if row["Estoque Atual"] < giro_medio:
                st.warning(f"{row['Produto']} → risco de ruptura")
            elif row["Estoque Atual"] > giro_medio * 1.5:
                st.info(f"{row['Produto']} → excesso de estoque")

        st.subheader("💰 Impacto Financeiro")
        fig, ax = plt.subplots()
        ax.bar(["Atual", "Otimizado"], [total, total * 0.8])
        st.pyplot(fig)

# ================= PRODUTOS =================
elif pagina == "📦 Produtos":

    st.title("📦 Análise de Produtos")

    if df is None:
        st.info("Envie a planilha")
    else:
        produto = st.selectbox("Produto", df["Produto"].unique())
        st.dataframe(df[df["Produto"] == produto])

# ================= FINANCEIRO =================
elif pagina == "💰 Financeiro":

    st.title("💰 Financeiro")

    if df is None:
        st.info("Envie a planilha")
    else:
        total = df["Valor Estoque"].sum()
        economia = total * 0.2

        col1, col2 = st.columns(2)
        col1.metric("Estoque", f"R$ {total:,.2f}")
        col2.metric("Economia", f"R$ {economia:,.2f}")

        fig, ax = plt.subplots()
        ax.pie([total * 0.8, economia], labels=["Otimizado", "Economia"], autopct='%1.1f%%')
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

        X = np.array(range(len(vendas))).reshape(-1, 1)
        modelo = LinearRegression().fit(X, vendas)
        previsao = modelo.predict([[len(vendas)]])[0]

        media = np.mean(vendas)

        col1, col2 = st.columns(2)
        col1.metric("📈 Previsão IA", round(previsao))
        col2.metric("📊 Média", round(media))

        if previsao > media:
            st.success("📈 Tendência de alta")
        elif previsao < media:
            st.warning("📉 Tendência de queda")
        else:
            st.info("➡️ Estável")

        # 🔥 GRÁFICO CORRIGIDO COM LEGENDA
        fig, ax = plt.subplots()

        ax.plot(vendas, marker='o', label="Histórico de Vendas")
        ax.axhline(previsao, linestyle='--', label="Previsão IA")

        ax.legend()
        ax.set_title("Tendência de Vendas")
        ax.set_xlabel("Período")
        ax.set_ylabel("Quantidade")

        st.pyplot(fig)

        st.caption("Linha contínua: histórico | Linha tracejada: previsão da IA")
