import sqlite3

# Define the database connection
conn = sqlite3.connect("stock_management.db")

# Create a cursor
cursor = conn.cursor()

# Create the Admin table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
""")

# Create the Empresa table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Empresa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    senha TEXT NOT NULL,
    proprietario TEXT NOT NULL,
    data_nascimento DATE NOT NULL,
    endereco TEXT NOT NULL,
    cnpj TEXT NOT NULL
)
""")

# Create the Collaborator table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Collaborator (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cargo TEXT NOT NULL,
    empresa_id INTEGER NOT NULL,
    FOREIGN KEY (empresa_id) REFERENCES Empresa (id)
)
""")

# Insert a sample admin user
cursor.execute("""
INSERT INTO Admin (username, password) 
VALUES ('admin', 'admin123')
""")

# Insert a sample company
cursor.execute("""
INSERT INTO Empresa (nome, senha, proprietario, data_nascimento, endereco, cnpj) 
VALUES ('LR System', '123', 'Lucas Ramalho', '1990-04-06', 'Terenos, MS', '12.345.678/0001-99')
""")

# Commit the changes and close the connection
conn.commit()
conn.close()