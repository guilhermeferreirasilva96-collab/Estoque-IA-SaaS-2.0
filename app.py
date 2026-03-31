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

# ---------------- SESSION STATE ----------------
for key in ['logado', 'empresa', 'usuario', 'login_user', 'login_senha', 'admin']:
    if key not in st.session_state:
        st.session_state[key] = False if key in ['logado', 'admin'] else ""

# ---------------- LOGIN ----------------
def login_usuario():
    user = st.session_state.get("login_user", "")
    password = st.session_state.get("login_senha", "")

    if not user or not password:
        st.warning("Preencha usuário e senha")
        return False

    user_clean = user.strip()
    password_clean = password.strip()
    password_hash = hash_senha(password_clean)

    cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (user_clean,))
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        if usuario_existente[3] == password_hash:
            st.session_state['logado'] = True
            st.session_state['empresa'] = usuario_existente[1]
            st.session_state['usuario'] = usuario_existente[2]

            # ADMIN
            st.session_state['admin'] = usuario_existente[2] == "Guilherme Ferreira"

            return True
        else:
            st.error("❌ Senha incorreta")
            return False
    else:
        st.error("❌ Usuário não encontrado")
        return False

# ---------------- LOGOUT ----------------
def logout_usuario():
    st.session_state['logado'] = False
    st.session_state['empresa'] = ""
    st.session_state['usuario'] = ""
    st.session_state['admin'] = False

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
        empresa = st.text_input("Empresa", key="cad_empresa")
        novo_user = st.text_input("Usuário", key="cad_user")
        nova_senha = st.text_input("Senha", type="password", key="cad_senha")
        codigo_convite = st.text_input("Código de convite", type="password")

        if st.button("Cadastrar"):
            if codigo_convite not in CODIGOS_VALIDOS and novo_user != "Guilherme Ferreira":
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

    # LOGIN
    with col2:
        st.subheader("🔐 Login")
        st.text_input("Usuário", key="login_user")
        st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            if login_usuario():
                st.success(f"✅ Bem-vindo {st.session_state['usuario']}")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
st.sidebar.markdown("## StockMind IA")

if st.session_state['empresa']:
    st.sidebar.success(f"Empresa: {st.session_state['empresa']}")

# ADMIN RESET
if st.session_state.get("admin", False):
    if st.sidebar.button("⚠️ Resetar usuários"):
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        st.success("Usuários resetados")

# LOGOUT
if st.sidebar.button("🚪 Sair"):
    logout_usuario()

# ---------------- UPLOAD ----------------
file = st.sidebar.file_uploader("📁 Upload", type=["xlsx", "csv"])

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df['Produto'] = df['Produto'].astype(str).str.strip()

    if "Valor Unitário" in df.columns:
        df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")
        df["Valor Estoque"] = df["Estoque Atual"] * df["Valor Unitário"]
    else:
        df["Valor Estoque"] = df["Estoque Atual"] * 50

    pagina = st.sidebar.radio("Menu", ["Dashboard", "Produtos", "IA"])

    if pagina == "Dashboard":
        st.title("📊 Dashboard")
        st.metric("Total Estoque", f"R$ {df['Valor Estoque'].sum():,.2f}")

    elif pagina == "Produtos":
        produto = st.selectbox("Produto", df["Produto"].unique())
        st.dataframe(df[df["Produto"] == produto])

    elif pagina == "IA":
        produto = st.selectbox("Produto", df["Produto"].unique())
        vendas = df[df["Produto"] == produto][['Venda Mês 1','Venda Mês 2','Venda Mês 3']].values.flatten()

        X = np.array(range(len(vendas))).reshape(-1, 1)
        modelo = LinearRegression().fit(X, vendas)
        previsao = int(modelo.predict([[len(vendas)]])[0])

        st.metric("Previsão IA", previsao)

else:
    st.info("Envie uma planilha")
