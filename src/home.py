import streamlit as st

# Check if the user is logged in
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.experimental_rerun("app.py")

# Create a Streamlit app
st.title("Página Inicial")

# Add a sidebar with user profile and navigation options
st.sidebar.title("Perfil do Usuário")
st.sidebar.image("path/to/profile_picture.jpg", width=100)  # Substitua pelo caminho da imagem do perfil
st.sidebar.write("Usuário: admin")

st.sidebar.title("Navegação")
page = st.sidebar.radio("Ir para", ["Agenda de Atribuições", "Cadastrar Empresa", "Cadastrar Colaborador", "Cadastrar Administrador"])

# Add a logout button
logout_button = st.sidebar.button("Logout")

# Handle navigation
if page == "Agenda de Atribuições":
    st.write("Aqui está a sua agenda de atribuições.")
elif page == "Cadastrar Empresa":
    st.experimental_rerun("register_company.py")
elif page == "Cadastrar Colaborador":
    st.experimental_rerun("register_collaborator.py")
elif page == "Cadastrar Administrador":
    st.experimental_rerun("register_admin.py")

# Handle logout button click
if logout_button:
    st.session_state.logged_in = False
    st.experimental_rerun("app.py")