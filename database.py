import streamlit as st
import sqlite3
import hashlib

def create_database():
    # Conexão com o banco de dados
    conn = sqlite3.connect("stock_management.db")
    cursor = conn.cursor()

    # Criação das tabelas
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS Empresa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL,
        proprietario TEXT NOT NULL,
        data_nascimento TEXT NOT NULL,
        endereco TEXT NOT NULL,
        cnpj TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Cargos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        accessible_pages TEXT
    );

    CREATE TABLE IF NOT EXISTS Collaborator (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        senha TEXT NOT NULL,
        matricula TEXT UNIQUE,
        cargo_id INTEGER NOT NULL,
        empresa_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        FOREIGN KEY (empresa_id) REFERENCES Empresa (id),
        FOREIGN KEY (cargo_id) REFERENCES Cargos (id)
    );

    CREATE TABLE IF NOT EXISTS Schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collaborator_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        commitment TEXT NOT NULL,
        FOREIGN KEY (collaborator_id) REFERENCES Collaborator (id)
    );

    CREATE TABLE IF NOT EXISTS Events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        event TEXT NOT NULL,
        FOREIGN KEY (empresa_id) REFERENCES Empresa (id)
    );
    """)
    conn.commit()

    # Inserção de Cargos padrão
    cargos = [
        ("Gerente de Logística", "agenda"),
        ("Analista de Logística", "agenda"),
        ("Coordenador de Transportes", "agenda"),
        ("Operador de Empilhadeira", "agenda"),
        ("Conferente de Carga", "agenda"),
        ("Auxiliar de Almoxarifado", "agenda"),
        ("Motorista", "agenda"),
        ("Técnico em Logística", "agenda"),
        ("Supervisor de Armazém", "agenda"),
        ("Especialista em Supply Chain", "agenda")
    ]
    for cargo, accessible_pages in cargos:
        cursor.execute("INSERT OR IGNORE INTO Cargos (nome, accessible_pages) VALUES (?, ?)", (cargo, accessible_pages))
    conn.commit()

    # Criar empresa padrão
    cursor.execute("SELECT COUNT(*) FROM Empresa WHERE nome = 'LR System'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO Empresa (nome, senha, proprietario, data_nascimento, endereco, cnpj)
        VALUES ('LR System', '123', 'Lucas Ramalho', '1990-04-06', 'Terenos, MS', '12.345.678/0001-99')
        """)
        conn.commit()

    # Obtém o ID da empresa recém-criada
    cursor.execute("SELECT id FROM Empresa WHERE nome = 'LR System'")
    empresa_id = cursor.fetchone()[0]

    # Criar usuário admin vinculado à empresa
    cursor.execute("SELECT COUNT(*) FROM Collaborator WHERE nome = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed_password = hashlib.sha256("123".encode()).hexdigest()
        cursor.execute("""
        INSERT INTO Collaborator (nome, senha, cargo_id, empresa_id, role)
        VALUES ('admin', ?, 1, ?, 'admin')
        """, (hashed_password, empresa_id))
        conn.commit()

        # Atualizar matrícula do admin (empresa_id + colaborador_id)
        cursor.execute("SELECT id FROM Collaborator WHERE nome = 'admin'")
        admin_id = cursor.fetchone()[0]
        matricula_admin = f"{empresa_id}{admin_id}"

        cursor.execute("UPDATE Collaborator SET matricula = ? WHERE id = ?", (matricula_admin, admin_id))
        conn.commit()

    # Criar agendamentos e eventos padrão
    cursor.execute("SELECT COUNT(*) FROM Schedule WHERE collaborator_id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO Schedule (collaborator_id, date, commitment)
        VALUES (1, '2025-02-01', 'Reunião de Projeto'),
               (1, '2025-02-02', 'Desenvolvimento de Funcionalidade X')
        """)
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM Events WHERE empresa_id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO Events (empresa_id, date, event)
        VALUES (1, '2025-02-03', 'Evento Corporativo Anual'),
               (1, '2025-02-04', 'Treinamento de Segurança')
        """)
        conn.commit()

    conn.close()
    return "Banco de dados criado e atualizado com sucesso!"

# Interface do Streamlit
st.title("📊 Configuração do Banco de Dados")

if st.button("Criar/Reiniciar Banco de Dados"):
    mensagem = create_database()
    st.success(mensagem)
