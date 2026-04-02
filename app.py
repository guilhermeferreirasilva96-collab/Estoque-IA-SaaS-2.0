import streamlit as st
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

# 🔥 GARANTE USUÁRIO PADRÃO NO DEPLOY
usuario_padrao = "guilherme ferreira"
senha_padrao = "260518Be!"
senha_hash = hashlib.sha256(senha_padrao.encode()).hexdigest()

cursor.execute(
    "SELECT * FROM usuarios WHERE LOWER(usuario)=?",
    (usuario_padrao,)
)

if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
        ("GB Multistore", usuario_padrao, senha_hash)
    )
    conn.commit()

# ---------------- HASH SENHA ----------------
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ---------------- SESSION ----------------
for chave, valor in {"logado": False, "empresa": ""}.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

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

    # ---------------- CADASTRO ----------------
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
                tipo_acesso = CODIGOS_VALIDOS[codigo_convite]

                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa.strip(), novo_user.strip(), hash_senha(nova_senha.strip()))
                )
                conn.commit()

                del CODIGOS_VALIDOS[codigo_convite]

                st.success(f"✅ Conta criada! Tipo de acesso: {tipo_acesso}")
            else:
                st.warning("Preencha todos os campos")

    # ---------------- LOGIN ----------------
    with col2:
        st.subheader("🔐 Login")

        user = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            user_clean = user.strip().lower()
            password_clean = password.strip()
            password_hash = hash_senha(password_clean)

            # Debug opcional
            st.write(f"Digitado: Usuário='{user.strip()}', Senha='{password_clean}'")
            st.write(f"Senha hash calculada: {password_hash}")

            cursor.execute(
                "SELECT * FROM usuarios WHERE LOWER(usuario)=?",
                (user_clean,)
            )
            usuario_existente = cursor.fetchone()

            if usuario_existente:
                if usuario_existente[3] == password_hash:
                    st.session_state.logado = True
                    st.session_state.empresa = usuario_existente[1]
                    st.success(f"✅ Login bem-sucedido! Bem-vindo(a) {usuario_existente[2]}")
                    st.rerun()
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
    st.session_state.logado = False
    st.session_state.empresa = ""
    st.rerun()
