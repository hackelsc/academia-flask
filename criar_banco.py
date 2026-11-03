import sqlite3
from werkzeug.security import generate_password_hash

conexao = sqlite3.connect("academia.db")
cursor = conexao.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_matricula TEXT,
        nome TEXT,
        cpf TEXT UNIQUE,
        telefone TEXT,
        email TEXT,
        rua TEXT,
        numero TEXT,
        complemento TEXT,
        bairro TEXT,
        cidade TEXT,
        uf TEXT,
        cep TEXT,
        nascimento DATE,
        mensalidade REAL,
        dia_vencimento INTEGER,
        data_matricula DATE,
        status INTEGER DEFAULT 1
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cpf TEXT UNIQUE,
        telefone TEXT,
        email TEXT,
        cargo TEXT,
        rua TEXT,
        numero TEXT,
        complemento TEXT,
        bairro TEXT,
        cidade TEXT,
        uf TEXT,
        cep TEXT,
        data_nascimento DATE,
        data_admissao DATE,
        status INTEGER DEFAULT 1
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS modalidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS turmas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modalidade_id INTEGER,
        funcionario_id INTEGER,
        dia_semana TEXT,
        horario_inicio TEXT,
        horario_fim TEXT,
        status INTEGER DEFAULT 1,
        FOREIGN KEY (modalidade_id) REFERENCES modalidades (id),
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios (id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS matriculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turma_id INTEGER,
        aluno_id INTEGER,
        FOREIGN KEY (turma_id) REFERENCES turmas (id),
        FOREIGN KEY (aluno_id) REFERENCES alunos (id) ON DELETE CASCADE
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        mes_referencia TEXT,
        valor REAL,
        data_pagamento DATE,
        forma_pagamento TEXT,
        status TEXT,
        FOREIGN KEY (aluno_id) REFERENCES alunos (id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        login TEXT UNIQUE,
        senha_hash TEXT,
        perfil TEXT
    )
""")
senha_hash_admin = generate_password_hash("trocar123")
cursor.execute(
    "INSERT OR IGNORE INTO usuarios (nome, login, senha_hash, perfil) VALUES (?, ?, ?, ?)",
    ("Administrador", "admin@academia.com", senha_hash_admin, "admin")
)

conexao.commit()
conexao.close()

print("Banco de dados criado com sucesso!")
