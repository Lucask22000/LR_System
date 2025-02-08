import streamlit as st
import sqlite3
import hashlib
from components.floating_chat import render_floating_chat

# Configuração da página sem sidebar
st.set_page_config(
    page_title="Sistema Logístico",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Esconder menu do Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def check_login(username, password):sword):
    conn = sqlite3.connect("stock_management.db")
    cursor = conn.cursor()
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()a256(password.encode()).hexdigest()
    cursor.execute("SELECT role FROM Collaborator WHERE matricula = ? AND senha = ?", ("SELECT role FROM Collaborator WHERE matricula = ? AND senha = ?", 
                  (username, hashed_password))assword))
    user = cursor.fetchone()ursor.fetchone()
    conn.close()
    
    return user[0] if user else None[0] if user else None

def main():
    col1, col2, col3 = st.columns([1, 2, 1])s([1, 2, 1])
    
    with col2:
        # Cabeçalho        # Cabeçalho
        st.title("🚛 LR System")
        st.header("Sistema Logístico")
        
        # Formulário de login    # Formulário de login
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Matrícula")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)it = st.form_submit_button("Entrar", use_container_width=True)
                    
            if submit:
                if not username or not password:           if not username or not password:
                    st.error("Preencha todos os campos")         st.error("Preencha todos os campos")
                else:
                    role = check_login(username, password)                role = check_login(username, password)
                    if role:      if role:
                        with st.spinner("Autenticando..."):
                            st.session_state["authenticated"] = Trueion_state["authenticated"] = True
                            st.session_state["role"] = rolerole
                            st.session_state["username"] = username                    st.session_state["username"] = username
                            st.success("Login realizado com sucesso!")cesso!")
                            st.switch_page("pages/home.py"))
                    else:
                        st.error("Matrícula ou senha incorretas")s")
    
    # Adicionar chat flutuante apenas se autenticadonar chat flutuante apenas se autenticado
    if st.session_state.get("authenticated"):
        render_floating_chat()

if __name__ == "__main__":
    main()