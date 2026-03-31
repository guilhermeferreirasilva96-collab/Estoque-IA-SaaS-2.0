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
            user_clean = user.strip().lower()  # normalize para minúsculas e remove espaços
            password_clean = password.strip()
            password_hash = hash_senha(password_clean)

            # Debug
            st.write(f"Digitado: Usuário='{user.strip()}', Senha='{password_clean}'")
            st.write(f"Senha hash calculada: {password_hash}")

            # Busca no banco ignorando maiúsculas/minúsculas
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
