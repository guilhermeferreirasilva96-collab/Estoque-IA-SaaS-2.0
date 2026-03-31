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

# ---------------- SESSION_STATE ----------------
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'empresa' not in st.session_state:
    st.session_state['empresa'] = ""

# ---------------- FUNÇÃO FORMATAÇÃO ----------------
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------------- FUNÇÃO RESETAR USUÁRIOS ----------------
def resetar_usuarios():
    cursor.execute("DELETE FROM usuarios")
    conn.commit()
    st.success("✅ Todos os usuários e senhas foram resetados!")

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
            # Permitir cadastro sem código apenas para "Guilherme Ferreira"
            if codigo_convite not in CODIGOS_VALIDOS and novo_user != "Guilherme Ferreira":
                st.error("❌ Código de convite inválido")
            elif empresa and novo_user and nova_senha:
                tipo_acesso = CODIGOS_VALIDOS[codigo_convite] if codigo_convite in CODIGOS_VALIDOS else "Admin"
                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa.strip(), novo_user.strip().lower(), hash_senha(nova_senha.strip()))
                )
                conn.commit()
                if codigo_convite in CODIGOS_VALIDOS:
                    del CODIGOS_VALIDOS[codigo_convite]
                st.success(f"✅ Conta criada! Tipo de acesso: {tipo_acesso}")
            else:
                st.warning("Preencha todos os campos")

        if st.button("⚠️ Resetar todos os usuários"):
            resetar_usuarios()

    # ---------------- LOGIN ----------------
    with col2:
        st.subheader("🔐 Login")
        user = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            user_clean = user.strip().lower()
            password_hash = hash_senha(password.strip())

            cursor.execute("SELECT * FROM usuarios WHERE LOWER(usuario)=?", (user_clean,))
            usuario_existente = cursor.fetchone()

            if usuario_existente:
                if usuario_existente[3] == password_hash:
                    st.session_state['logado'] = True
                    st.session_state['empresa'] = usuario_existente[1]
                    st.success(f"✅ Login bem-sucedido! Bem-vindo(a) {usuario_existente[2]}")
                    st.experimental_rerun()
                else:
                    st.error("❌ Senha incorreta")
            else:
                st.error("❌ Usuário não encontrado")

    st.markdown("---")
    st.caption("© 2026 StockMind IA • Todos os direitos reservados")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
st.sidebar.markdown("## StockMind IA")
st.sidebar.caption("Gestão inteligente de estoque")

empresa_nome = st.session_state.get("empresa", "")
if empresa_nome:
    st.sidebar.success(f"Empresa: {empresa_nome}")

if st.sidebar.button("🚪 Sair"):
    st.session_state['logado'] = False
    st.session_state['empresa'] = ""
    st.experimental_rerun()

pagina = st.sidebar.radio(
    "Menu",
    ["🏠 Visão Geral", "📦 Produtos", "💰 Financeiro", "🤖 IA"]
)

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

    # ================= VISÃO GERAL =================
    if pagina == "🏠 Visão Geral":
        st.subheader("📊 Dashboard Executivo")
        total = df["Valor Estoque"].sum()
        economia = total * 0.2
        giro_medio = df["Estoque Atual"].mean()
        ruptura = len(df[df["Estoque Atual"] < giro_medio])
        excesso = len(df[df["Estoque Atual"] > giro_medio * 1.5])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Estoque Total", formatar_real(total))
        col2.metric("📉 Economia Potencial", formatar_real(economia), "20%")
        col3.metric("⚠️ Risco de Ruptura", ruptura)
        col4.metric("📦 Excesso de Estoque", excesso)

        if ruptura > 0:
            st.warning(f"⚠️ {ruptura} produtos com risco de ruptura")

        st.divider()
        st.subheader("💰 Impacto Financeiro")
        fig1, ax1 = plt.subplots()
        ax1.bar(["Atual", "Otimizado"], [total, total * 0.8])
        st.pyplot(fig1)

        st.subheader("🏆 Top 5 Produtos (Valor em Estoque)")
        top = df.sort_values(by="Valor Estoque", ascending=False).head(5)
        st.dataframe(top[["Produto", "Valor Estoque"]])

        st.subheader("📊 Distribuição de Estoque")
        fig2, ax2 = plt.subplots()
        ax2.hist(df["Estoque Atual"], bins=10)
        st.pyplot(fig2)

    # ================= PRODUTOS =================
    elif pagina == "📦 Produtos":
        st.subheader("📦 Análise de Produtos")
        produto = st.selectbox("Produto", df["Produto"].unique())
        st.dataframe(df[df["Produto"] == produto])

    # ================= FINANCEIRO =================
    elif pagina == "💰 Financeiro":
        st.subheader("💰 Financeiro")
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
        previsao_final = round(previsao)
        media = np.mean(vendas)

        col1, col2 = st.columns(2)
        col1.metric("📈 Previsão (IA)", previsao_final)
        col2.metric("📊 Média Histórica", round(media))
        st.caption(f"Valor calculado pela IA: {previsao:.2f}")

        st.markdown("### 💡 Como a IA calcula?")
        st.info(
            "A IA analisa a tendência das vendas dos últimos períodos. "
            "Se as vendas estão crescendo, a previsão aumenta. "
            "Se estão caindo, a previsão reduz."
        )

        if previsao_final > media:
            st.success("📈 Tendência de alta nas vendas")
        elif previsao_final < media:
            st.warning("📉 Tendência de queda nas vendas")
        else:
            st.info("➡️ Vendas estáveis")

        st.subheader("📊 Tendência de Vendas")
        fig, ax = plt.subplots()
        ax.plot(vendas, marker='o', label="Histórico")
        ax.axhline(previsao, linestyle='--', label="Previsão IA")
        ax.legend()
        st.pyplot(fig)

else:
    st.info("👈 Envie a planilha para começar")
