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
                # Determina tipo de acesso
                tipo_acesso = CODIGOS_VALIDOS[codigo_convite] if codigo_convite in CODIGOS_VALIDOS else "Admin"
                cursor.execute(
                    "INSERT INTO usuarios (empresa, usuario, senha) VALUES (?, ?, ?)",
                    (empresa.strip(), novo_user.strip().lower(), hashlib.sha256(nova_senha.strip().encode()).hexdigest())
                )
                conn.commit()
                if codigo_convite in CODIGOS_VALIDOS:
                    del CODIGOS_VALIDOS[codigo_convite]
                st.success(f"✅ Conta criada! Tipo de acesso: {tipo_acesso}")
            else:
                st.warning("Preencha todos os campos")

        # ---------------- RESETAR USUÁRIOS ----------------
        if st.button("⚠️ Resetar todos os usuários"):
            cursor.execute("DELETE FROM usuarios")
            conn.commit()
            st.success("✅ Todos os usuários e senhas foram resetados!")

    # ---------------- LOGIN ----------------
    with col2:
        st.subheader("🔐 Login")
        user = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_senha")

        if st.button("Entrar"):
            user_clean = user.strip().lower()
            password_clean = password.strip()
            password_hash = hashlib.sha256(password_clean.encode()).hexdigest()

            cursor.execute("SELECT * FROM usuarios WHERE LOWER(usuario)=?", (user_clean,))
            usuario_existente = cursor.fetchone()

            if usuario_existente:
                if usuario_existente[3] == password_hash:
                    # Atualiza session_state antes do rerun
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
