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

# ---------------- SESSION STATE ----------------
for key in ['logado', 'empresa', 'usuario', 'login_user', 'login_senha']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'logado' else ""

# ---------------- LOGIN ----------------
def login_usuario():
    user = st.session_state.get("login_user", "")
    password = st.session_state.get("login_senha", "")

    if not user or not password:
        st.warning("Preencha usuário e senha")
        return False

    password_hash = hash_senha(password.strip())

    cursor.execute("SELECT * FROM usuarios WHERE usuario=?", (user.strip(),))
    usuario = cursor.fetchone()

    if usuario and usuario[3] == password_hash:
        st.session_state['logado'] = True
        st.session_state['empresa'] = usuario[1]
        st.session_state['usuario'] = usuario[2]
        return True
    else:
        st.error("❌ Usuário ou senha inválidos")
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

    # ---------------- CADASTRO ----------------
    with col1:
        st.subheader("📝 Criar conta")
        empresa = st.text_input("Empresa")
        novo_user = st.text_input("Usuário")
        nova_senha = st.text_input("Senha", type="password")
        codigo_convite = st.text_input("Código de convite", type="password")

        if st.button("Cadastrar"):
            if codigo_convite not in CODIGOS_VALIDOS and novo_user != "Guilherme Ferreira":
                st.error("❌ Código inválido")
            elif empresa and novo_user and nova_senha:
                tipo = CODIGOS_VALIDOS[codigo_convite] if codigo_convite in CODIGOS_VALIDOS else "Admin"

                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa.strip(), novo_user.strip(), hash_senha(nova_senha.strip()))
                )
                conn.commit()

                if codigo_convite in CODIGOS_VALIDOS:
                    del CODIGOS_VALIDOS[codigo_convite]

                st.success(f"✅ Conta criada! Tipo: {tipo}")
            else:
                st.warning("Preencha todos os campos")

    # ---------------- LOGIN ----------------
    with col2:
        st.subheader("🔐 Login")
        st.text_input("Usuário", key="login_user")
        st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            if login_usuario():
                st.success(f"Bem-vindo {st.session_state['usuario']}")
                st.stop()  # 🔥 resolve o problema de duplo clique

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## StockMind IA")

if st.session_state['empresa']:
    st.sidebar.success(f"Empresa: {st.session_state['empresa']}")

# ---------------- RESET ADMIN ----------------
if st.session_state['usuario'] == "Guilherme Ferreira":
    if st.sidebar.button("⚠️ Resetar usuários"):
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        st.success("Reset realizado")

# ---------------- LOGOUT ----------------
if st.sidebar.button("🚪 Sair"):
    logout_usuario()
    st.stop()  # 🔥 resolve 100% o problema

# ---------------- UPLOAD ----------------
file = st.sidebar.file_uploader("Upload", type=["xlsx", "csv"])

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df.columns = df.columns.str.strip()

    if "Valor Unitário" in df.columns:
        df["Valor Estoque"] = df["Estoque Atual"] * df["Valor Unitário"]
    else:
        df["Valor Estoque"] = df["Estoque Atual"] * 50

    pagina = st.sidebar.radio("Menu", ["Visão Geral", "IA"])

    if pagina == "Visão Geral":
        st.metric("Estoque Total", f"R$ {df['Valor Estoque'].sum():,.2f}")

    if pagina == "IA":
        vendas = df[['Venda Mês 1','Venda Mês 2','Venda Mês 3']].values.flatten()
        X = np.arange(len(vendas)).reshape(-1,1)
        modelo = LinearRegression().fit(X, vendas)
        previsao = modelo.predict([[len(vendas)]])[0]

        st.metric("Previsão IA", round(previsao))
