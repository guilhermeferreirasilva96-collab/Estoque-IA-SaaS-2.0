# ---------------- LOGIN ----------------
with col2:
    st.subheader("🔐 Login")

    user = st.text_input("Usuário", key="login_user")
    password = st.text_input("Senha", type="password", key="login_senha")

    if st.button("Entrar"):
        senha_hash = hash_senha(password.strip())

        cursor.execute(
            "SELECT * FROM usuarios WHERE TRIM(usuario)=? AND senha=?",
            (user.strip(), senha_hash)
        )
        result = cursor.fetchone()

        if result:
            st.session_state.logado = True
            st.session_state.empresa = result[1]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")
