# ---------------- LOGIN / CADASTRO ----------------
if not st.session_state.logado:

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
            if not (empresa and novo_user and nova_senha):
                st.warning("Preencha todos os campos")
            elif codigo_convite not in CODIGOS_VALIDOS and novo_user != "Guilherme Ferreira":
                st.error("❌ Código de convite inválido")
            else:
                tipo_acesso = CODIGOS_VALIDOS.get(codigo_convite, "Administrador")
                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa.strip(), novo_user.strip().lower(), hash_senha(nova_senha.strip()))
                )
                conn.commit()
                if codigo_convite in CODIGOS_VALIDOS:
                    del CODIGOS_VALIDOS[codigo_convite]
                st.success(f"✅ Conta criada! Tipo de acesso: {tipo_acesso}")
                st.info("Agora faça login à direita 👈")

        if st.button("⚠️ Resetar todos os usuários"):
            resetar_usuarios()

    # ---------------- LOGIN ----------------
    with col2:
        st.subheader("🔐 Login")
        user = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            if not (user and password):
                st.warning("Preencha usuário e senha")
            else:
                user_clean = user.strip().lower()
                password_hash = hash_senha(password.strip())

                cursor.execute("SELECT * FROM usuarios WHERE LOWER(usuario)=?", (user_clean,))
                usuario_existente = cursor.fetchone()

                if usuario_existente:
                    if usuario_existente[3] == password_hash:
                        st.session_state.logado = True
                        st.session_state.empresa = usuario_existente[1]
                        st.success(f"✅ Login bem-sucedido! Bem-vindo(a) {usuario_existente[2]}")
                        st.experimental_rerun()  # só é chamado aqui, com login válido
                    else:
                        st.error("❌ Senha incorreta")
                else:
                    st.error("❌ Usuário não encontrado")
