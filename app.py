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
    usuario_existente = cursor.fetchone()

    if usuario_existente and usuario_existente[3] == password_hash:
        st.session_state['logado'] = True
        st.session_state['empresa'] = usuario_existente[1]
        st.session_state['usuario'] = usuario_existente[2]
        return True

    st.error("❌ Usuário ou senha incorretos")
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
        empresa = st.text_input("Empresa", key="cad_empresa")
        novo_user = st.text_input("Usuário", key="cad_user")
        nova_senha = st.text_input("Senha", type="password", key="cad_senha")
        codigo_convite = st.text_input("Código de convite", type="password")

        if st.button("Cadastrar"):
            if codigo_convite not in CODIGOS_VALIDOS and novo_user != "Guilherme Ferreira":
                st.error("❌ Código de convite inválido")
            elif empresa and novo_user and nova_senha:
                tipo_acesso = CODIGOS_VALIDOS[codigo_convite] if codigo_convite in CODIGOS_VALIDOS else "Admin"

                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa.strip(), novo_user.strip(), hash_senha(nova_senha.strip()))
                )
                conn.commit()

                if codigo_convite in CODIGOS_VALIDOS:
                    del CODIGOS_VALIDOS[codigo_convite]

                st.success(f"✅ Conta criada! Tipo de acesso: {tipo_acesso}")
            else:
                st.warning("Preencha todos os campos")

    # ---------------- LOGIN ----------------
    with col2:
        st.subheader("🔐 Login")
        st.text_input("Usuário", key="login_user")
        st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            if login_usuario():
                st.success(f"✅ Bem-vindo(a) {st.session_state['usuario']}")
                st.rerun()

    st.markdown("---")
    st.caption("© 2026 StockMind IA • Todos os direitos reservados")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
st.sidebar.markdown("## StockMind IA")
st.sidebar.caption("Gestão inteligente de estoque")

empresa_nome = st.session_state.get("empresa", "")
usuario_logado = st.session_state.get("usuario", "")

if empresa_nome:
    st.sidebar.success(f"Empresa: {empresa_nome}")

# ---------------- RESET (ADMIN) ----------------
if usuario_logado == "Guilherme Ferreira":
    if st.sidebar.button("⚠️ Resetar usuários"):
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        st.success("✅ Usuários resetados!")

# ---------------- LOGOUT ----------------
if st.sidebar.button("🚪 Sair"):
    logout_usuario()
    st.rerun()

# ---------------- UPLOAD ----------------
file = st.sidebar.file_uploader("📁 Upload da planilha", type=["xlsx", "csv"])

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df['Produto'] = df['Produto'].astype(str).str.strip()

    # ---------------- VALOR ESTOQUE ----------------
    if "Valor Unitário" in df.columns:
        df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")
        df["Valor Estoque"] = df["Estoque Atual"] * df["Valor Unitário"]
    elif "Valor Unitario" in df.columns:
        df["Valor Unitario"] = pd.to_numeric(df["Valor Unitario"], errors="coerce")
        df["Valor Estoque"] = df["Estoque Atual"] * df["Valor Unitario"]
    else:
        st.warning("⚠️ Coluna 'Valor Unitário' não encontrada. Usando valor padrão de R$ 50.")
        df["Valor Estoque"] = df["Estoque Atual"] * 50.0

    # ================= MENU =================
    pagina = st.sidebar.radio("Menu", ["🏠 Visão Geral", "📦 Produtos", "💰 Financeiro", "🤖 IA"])

    if pagina == "🏠 Visão Geral":
        st.subheader("📊 Dashboard Executivo")
        total = df["Valor Estoque"].sum()
        economia = total * 0.2

        col1, col2 = st.columns(2)
        col1.metric("💰 Estoque Total", f"R$ {total:,.2f}")
        col2.metric("📉 Economia", f"R$ {economia:,.2f}")

    elif pagina == "📦 Produtos":
        produto = st.selectbox("Produto", df["Produto"].unique())
        st.dataframe(df[df["Produto"] == produto])

    elif pagina == "💰 Financeiro":
        total = df["Valor Estoque"].sum()
        economia = total * 0.2
        st.metric("💰 Total", f"R$ {total:,.2f}")
        st.metric("📉 Economia", f"R$ {economia:,.2f}")

    elif pagina == "🤖 IA":
        produto = st.selectbox("Produto", df["Produto"].unique())
        vendas = df[df["Produto"] == produto][['Venda Mês 1', 'Venda Mês 2', 'Venda Mês 3']].values.flatten()

        X = np.array(range(len(vendas))).reshape(-1, 1)
        modelo = LinearRegression().fit(X, vendas)
        previsao = round(modelo.predict([[len(vendas)]])[0])

        st.metric("📈 Previsão", previsao)

else:
    st.info("👈 Envie uma planilha para começar")
