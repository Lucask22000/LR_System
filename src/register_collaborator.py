import streamlit as st
import sqlite3

# Define the database connection
conn = sqlite3.connect("stock_management.db")

# Create a Streamlit app
st.title("Cadastro de Colaborador")

# Add a text input for collaborator name
collaborator_name = st.text_input("Nome do Colaborador")

# Add a text input for collaborator role
collaborator_role = st.text_input("Cargo do Colaborador")

# Add a selectbox for company
cursor = conn.cursor()
cursor.execute("SELECT id, nome FROM Empresa")
companies = cursor.fetchall()
company_options = {name: id for id, name in companies}
company_name = st.selectbox("Empresa", list(company_options.keys()))

# Add a register button
register_button = st.button("Cadastrar")

# Define a function to register collaborator
def register_collaborator(name, role, company_id):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Collaborator (nome, cargo, empresa_id) 
        VALUES (?, ?, ?)
    """, (name, role, company_id))
    conn.commit()

# Handle register button click
if register_button:
    if collaborator_name and collaborator_role and company_name:
        register_collaborator(collaborator_name, collaborator_role, company_options[company_name])
        st.success("Colaborador cadastrado com sucesso!")
    else:
        st.error("Por favor, preencha todos os campos.")