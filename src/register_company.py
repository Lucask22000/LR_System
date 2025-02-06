import streamlit as st
import sqlite3

# Define the database connection
conn = sqlite3.connect("stock_management.db")

# Create a Streamlit app
st.title("Cadastro de Empresa")

# Add a text input for company name
company_name = st.text_input("Nome da Empresa")

# Add a text input for company password
company_password = st.text_input("Senha da Empresa", type="password")

# Add a text input for company owner
company_owner = st.text_input("Proprietário da Empresa")

# Add a date input for company owner's birth date
company_owner_birth_date = st.date_input("Data de Nascimento do Proprietário")

# Add a text input for company address
company_address = st.text_input("Endereço da Empresa")

# Add a text input for company CNPJ
company_cnpj = st.text_input("CNPJ da Empresa")

# Add a register button
register_button = st.button("Cadastrar")

# Define a function to register company
def register_company(name, password, owner, birth_date, address, cnpj):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Empresa (nome, senha, proprietario, data_nascimento, endereco, cnpj) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, password, owner, birth_date, address, cnpj))
    conn.commit()

# Handle register button click
if register_button:
    if company_name and company_password and company_owner and company_owner_birth_date and company_address and company_cnpj:
        register_company(company_name, company_password, company_owner, company_owner_birth_date, company_address, company_cnpj)
        st.success("Empresa cadastrada com sucesso!")
    else:
        st.error("Por favor, preencha todos os campos.")