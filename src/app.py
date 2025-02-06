# Import libraries
import streamlit as st
import sqlite3

# Define the database connection
conn = sqlite3.connect("stock_management.db")

# Create a Streamlit app
st.title("Sistema Logístico - Login")

# Add a text input for username
username = st.text_input("Usuário")

# Add a text input for password
password = st.text_input("Senha", type="password")

# Add a login button
login_button = st.button("Login")

# Define a function to validate login
def validate_login(username, password):
    # Query the database for the admin user
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Admin WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    return user

# Handle login button click
if login_button:
    user = validate_login(username, password)
    if user:
        st.session_state.logged_in = True
        st.experimental_rerun("home.py")
    else:
        st.error("Usuário ou senha incorretos.")