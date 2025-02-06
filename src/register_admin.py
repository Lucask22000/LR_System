import streamlit as st
import sqlite3

# Define the database connection
conn = sqlite3.connect("stock_management.db")

# Create a Streamlit app
st.title("Cadastro de Administrador")

# Add a text input for admin username
admin_username = st.text_input("Nome de Usuário do Administrador")

# Add a text input for admin password
admin_password = st.text_input("Senha do Administrador", type="password")

# Add a register button
register_button = st.button("Cadastrar")

# Define a function to register admin
def register_admin(username, password):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Admin (username, password) 
        VALUES (?, ?)
    """, (username, password))
    conn.commit()

# Handle register button click
if register_button:
    if admin_username and admin_password:
        register_admin(admin_username, admin_password)
        st.success("Administrador cadastrado com sucesso!")
    else:
        st.error("Por favor, preencha todos os campos.")