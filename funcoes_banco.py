import os
import psycopg
from psycopg.types.numeric import FloatLoader
from datetime import date

####################
# Funções de apoio #
####################

def conectar():
    '''Abre a conexão com o PostgreSQL usando o endereço guardado em DATABASE_URL (arquivo .env).
       O valor é lido aqui dentro (e não no topo do arquivo) porque o app.py importa este
       arquivo antes de chamar o load_dotenv().
    '''
    conexao = psycopg.connect(os.environ["DATABASE_URL"])
    # NUMERIC (dinheiro) volta como número comum (float), igual era no SQLite
    conexao.adapters.register_loader("numeric", FloatLoader)
    return conexao


def buscar_todos(sql, parametros = ()):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(sql, parametros)
    resposta = cursor.fetchall()

    conexao.close()
    return resposta


def buscar_um(sql, parametros = ()):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(sql, parametros)
    resposta = cursor.fetchone()

    conexao.close()
    return resposta

def executar(sql, parametros):
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(sql, parametros)

    conexao.commit()
    conexao.close()
    return



####################
# Funções Alunos #
####################

def gerar_numero_matricula():
    '''1) Pega o último valor de matrícula existente no DB, do ano atual
       2) Se não encontrar nenhum (resultado is None), proximo_valor_sequencia = 1
       3) Se encontrar, exclui o ano e pega só a sequência numérica (a partir do quarto dígito [4:]),
          soma 1 pra achar o próximo valor
       4) resultado final = concatenação do ano_atual + proximo_valor_sequencia
    '''

    ano_atual = date.today().year

    resultado = buscar_um("SELECT numero_matricula FROM alunos WHERE numero_matricula ILIKE %s ORDER BY numero_matricula DESC LIMIT 1",
        (f"{ano_atual}%",))

    if resultado is None:
        proximo_valor_sequencia = 1
    else:
        ultima_matricula = resultado[0]  # primeiro argumento da tupla resultante (ARGUMENTO 1  , argumento 2)
        ultimo_valor_sequencia = int(ultima_matricula[4:])  # tira os 4 dígitos do ano, sobra a sequência
        proximo_valor_sequencia = ultimo_valor_sequencia + 1

    return f"{ano_atual}{proximo_valor_sequencia:03d}"

def cadastrar_aluno(nome, cpf, telefone, email, rua, numero, complemento, bairro, cidade, uf, cep, nascimento, mensalidade, dia_vencimento, status):

    numero_matricula = gerar_numero_matricula()
    data_matricula = date.today().isoformat()

    return executar("INSERT INTO alunos (numero_matricula, nome, cpf, telefone, email, rua, numero, complemento, bairro, cidade, uf, cep, nascimento, mensalidade, dia_vencimento, data_matricula, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (numero_matricula, nome, cpf, telefone, email, rua, numero, complemento, bairro, cidade, uf, cep, nascimento, mensalidade, dia_vencimento, data_matricula, status)
            )

def buscar_aluno(id):
    ''' Necessária nas rotas de editar e excluir.'''
    return buscar_um("SELECT id, numero_matricula, nome, cpf, telefone, email, rua, numero, complemento, bairro, cidade, uf, cep, nascimento, mensalidade, dia_vencimento, data_matricula, status FROM alunos WHERE id = %s",
                     (id,))

def buscar_aluno_por_cpf(cpf):
    '''Usada para impedir dois alunos com o mesmo CPF. Recebe só os números.'''
    return buscar_um("SELECT id, nome FROM alunos WHERE cpf = %s",
                     (cpf,))

def filtrar_alunos(termo="", status=""):
    sql = "SELECT * FROM alunos WHERE 1 = 1"
    parametros = []
    if termo:
        sql += """ AND (numero_matricula ILIKE %s OR nome ILIKE %s OR telefone ILIKE %s
                   OR email ILIKE %s OR rua ILIKE %s OR bairro ILIKE %s OR cidade ILIKE %s"""
        termo_like = f"%{termo}%"
        parametros += [termo_like] * 7
        so_numeros = "".join(c for c in termo if c.isdigit())
        if so_numeros:
            sql += " OR cpf ILIKE %s"
            parametros.append(f"%{so_numeros}%")
        sql += ")"
    if status in ("0", "1"):
        sql += " AND status = %s"
        parametros.append(int(status))
    return buscar_todos(sql, tuple(parametros))

def atualizar_aluno(numero_matricula, nome, cpf, telefone, email, rua, numero, complemento, bairro, cidade, uf, cep, nascimento, mensalidade, dia_vencimento, data_matricula, status, id):
    return executar(
        "UPDATE alunos SET numero_matricula = %s, nome = %s, cpf = %s, telefone = %s, email = %s, rua = %s, numero = %s, complemento = %s, bairro = %s, cidade = %s, uf = %s, cep = %s, nascimento = %s, mensalidade = %s, dia_vencimento = %s, data_matricula = %s, status = %s WHERE id = %s",
        (numero_matricula, nome, cpf, telefone, email, rua, numero, complemento, bairro, cidade, uf, cep, nascimento, mensalidade, dia_vencimento, data_matricula, status, id)
    )

def inativar_aluno(id):
    return executar("UPDATE alunos SET status = 0 WHERE id = %s",
                    (id,)
    )

def reativar_aluno(id):
    return executar("UPDATE alunos SET status = 1 WHERE id = %s",
                    (id,)
    )

#######################
# Funções Funcionários #
#######################

def cadastrar_funcionario(nome, cpf, telefone, email, cargo, rua, numero, complemento, bairro, cidade, uf, cep, data_nascimento, data_admissao, status):

    return executar("INSERT INTO funcionarios (nome, cpf, telefone, email, cargo, rua, numero, complemento, bairro, cidade, uf, cep, data_nascimento, data_admissao, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (nome, cpf, telefone, email, cargo, rua, numero, complemento, bairro, cidade, uf, cep, data_nascimento, data_admissao, status)
    )

def listar_funcionarios():
    return(buscar_todos("SELECT * FROM funcionarios"))

def buscar_funcionario(id):
    ''' Necessária nas rotas de editar, inativar e reativar.'''
    return buscar_um("SELECT id, nome, cpf, telefone, email, cargo, rua, numero, complemento, bairro, cidade, uf, cep, data_nascimento, data_admissao, status FROM funcionarios WHERE id = %s",
                     (id,)
    )

def buscar_funcionario_por_cpf(cpf):
    '''Usada para impedir dois funcionários com o mesmo CPF. Recebe só os números.'''
    return buscar_um("SELECT id, nome FROM funcionarios WHERE cpf = %s",
                     (cpf,))

def filtrar_funcionarios(termo="", status="", cargo=""):
    sql = "SELECT * FROM funcionarios WHERE 1 = 1"
    parametros = []

    if termo:
        sql += """ AND (nome ILIKE %s OR telefone ILIKE %s OR email ILIKE %s OR cargo ILIKE %s
                   OR rua ILIKE %s OR bairro ILIKE %s OR cidade ILIKE %s"""
        termo_like = f"%{termo}%"
        parametros += [termo_like] * 7
        so_numeros = "".join(c for c in termo if c.isdigit())
        if so_numeros:
            sql += " OR cpf ILIKE %s"
            parametros.append(f"%{so_numeros}%")
        sql += ")"

    if status in ("0", "1"):
        sql += " AND status = %s"
        parametros.append(int(status))

    if cargo:
        sql += " AND cargo = %s"
        parametros.append(cargo)

    return buscar_todos(sql, tuple(parametros))

def atualizar_funcionario(nome, cpf, telefone, email, cargo, rua, numero, complemento, bairro, cidade, uf, cep, data_nascimento, data_admissao, status, id):
    return executar(
        "UPDATE funcionarios SET nome = %s, cpf = %s, telefone = %s, email = %s, cargo = %s, rua = %s, numero = %s, complemento = %s, bairro = %s, cidade = %s, uf = %s, cep = %s, data_nascimento = %s, data_admissao = %s, status = %s WHERE id = %s",
        (nome, cpf, telefone, email, cargo, rua, numero, complemento, bairro, cidade, uf, cep, data_nascimento, data_admissao, status, id)
    )

def inativar_funcionario(id):
    return executar("UPDATE funcionarios SET status = 0 WHERE id = %s",
                    (id,)
    )

def reativar_funcionario(id):
    return executar("UPDATE funcionarios SET status = 1 WHERE id = %s",
                    (id,)
    )

######################
# Função Modalidades #
######################

def listar_modalidades():
    return(buscar_todos("SELECT * FROM modalidades"))

def cadastrar_modalidade(nome):
    return executar("INSERT INTO modalidades (nome) VALUES (%s)",
                    (nome,)
    )

def buscar_modalidade(id):
    return buscar_um("SELECT id, nome FROM modalidades WHERE id = %s",
                     (id,)
    )

def atualizar_modalidade(id, nome):
    return executar("UPDATE modalidades SET nome = %s WHERE id = %s",
                    (nome, id)
    )

def deletar_modalidade(id):
    '''Remove a modalidade do banco. ATENCAO: se alguma turma usar a modalidade,
    o banco bloqueia o delete (erro). A rota conferir as turmas antes de chamar esta funcao.'''
    return executar("DELETE FROM modalidades WHERE id = %s",
                    (id,)
    )

#################
# Funções Turmas #
#################

def cadastrar_turma(modalidade_id, funcionario_id, dia_semana, horario_inicio, horario_fim, status):
    return executar(
        "INSERT INTO turmas (modalidade_id, funcionario_id, dia_semana, horario_inicio, horario_fim, status) VALUES (%s, %s, %s, %s, %s, %s)",
        (modalidade_id, funcionario_id, dia_semana, horario_inicio, horario_fim, status)
    )

def filtrar_turmas(modalidade_id="", funcionario_id="", dia_semana="", status=""):
    sql = """SELECT t.id, m.nome, f.nome, t.dia_semana, t.horario_inicio, t.horario_fim, t.status
             FROM turmas t
             JOIN modalidades m ON m.id = t.modalidade_id
             LEFT JOIN funcionarios f ON f.id = t.funcionario_id
             WHERE 1 = 1"""
    parametros = []

    if modalidade_id.isdigit():
        sql += " AND t.modalidade_id = %s"
        parametros.append(int(modalidade_id))

    if funcionario_id.isdigit():
        sql += " AND t.funcionario_id = %s"
        parametros.append(int(funcionario_id))

    if dia_semana:
        sql += " AND t.dia_semana ILIKE %s"
        parametros.append("%" + dia_semana + "%")

    if status in ("0", "1"):
        sql += " AND t.status = %s"
        parametros.append(int(status))

    return buscar_todos(sql, tuple(parametros))


def listar_turmas_por_modalidade(modalidade_id):
    '''filtro por id já conhecido'''
    return buscar_todos(
        """SELECT t.id, f.nome, t.dia_semana, t.horario_inicio, t.horario_fim, t.status
           FROM turmas t
           JOIN funcionarios f ON f.id = t.funcionario_id
           WHERE t.modalidade_id = %s""",
        (modalidade_id,)
    )

def buscar_turma(id):
    ''' Necessária nas rotas de editar e excluir.
    Sem JOIN, para o formulário de edição.'''
    return buscar_um("SELECT id, modalidade_id, funcionario_id, dia_semana, horario_inicio, horario_fim, status FROM turmas WHERE id = %s",
                     (id,)
    )


def atualizar_turma(id, modalidade_id, funcionario_id, dia_semana, horario_inicio, horario_fim, status):
    return executar(
        """UPDATE turmas
           SET modalidade_id = %s, funcionario_id = %s, dia_semana = %s, horario_inicio = %s, horario_fim = %s, status = %s
           WHERE id = %s""",
        (modalidade_id, funcionario_id, dia_semana, horario_inicio, horario_fim, status, id)
    )

def inativar_turma(id):
    return executar("UPDATE turmas SET status = 0 WHERE id = %s", (id,))

def reativar_turma(id):
    return executar("UPDATE turmas SET status = 1 WHERE id = %s", (id,))

def deletar_turma(id):
    '''Remove a turma do banco. ATENCAO: se ela tiver matriculas associadas,
    vai dar erro (a decisao do que fazer nesse caso ainda nao foi tomada).'''
    return executar("DELETE FROM turmas WHERE id = %s", (id,))

#####################
# Funções Matriculas #
#####################

def matricular_aluno(turma_id, aluno_id):
    return executar(
        "INSERT INTO matriculas (turma_id, aluno_id) VALUES (%s, %s)",
        (turma_id, aluno_id)
    )

def listar_alunos_por_turma(turma_id):
    '''Busca os alunos matriculados numa turma, para listar na tela.
    Inclui m.id (id da matricula) porque desmatricular_aluno(id) apaga por esse id, nao pelo id do aluno.'''
    return buscar_todos(
        """SELECT m.id, a.id, a.numero_matricula, a.nome, a.telefone
           FROM matriculas m
           JOIN alunos a ON a.id = m.aluno_id
           WHERE m.turma_id = %s""",
        (turma_id,)
    )

def listar_turmas_por_aluno(aluno_id):
    '''Inclui mt.id (id da matricula) porque desmatricular_aluno(id) apaga por esse id, nao pelo id da turma.'''
    return buscar_todos(
        """SELECT mt.id, t.id, m.nome, f.nome, t.dia_semana, t.horario_inicio, t.horario_fim
           FROM matriculas mt
           JOIN turmas t ON t.id = mt.turma_id
           JOIN modalidades m ON m.id = t.modalidade_id
           LEFT JOIN funcionarios f ON f.id = t.funcionario_id
           WHERE mt.aluno_id = %s""",
        (aluno_id,)
    )

def desmatricular_aluno(id):
    return executar("DELETE FROM matriculas WHERE id = %s", (id,))

######################
# Funções Pagamentos #
######################

def registrar_pagamento(aluno_id, mes_referencia, valor, forma_pagamento):
    data_pagamento = date.today().isoformat()
    status = "pago"
    return executar(
        "INSERT INTO pagamentos (aluno_id, mes_referencia, valor, data_pagamento, forma_pagamento, status) VALUES (%s, %s, %s, %s, %s, %s)",
        (aluno_id, mes_referencia, valor, data_pagamento, forma_pagamento, status)
    )

def listar_pagamentos(termo=""):
    sql = """SELECT p.id, a.nome, p.mes_referencia, p.valor, p.data_pagamento, p.forma_pagamento, p.status
             FROM pagamentos p
             JOIN alunos a ON a.id = p.aluno_id
             WHERE 1 = 1"""
    parametros = []
    if termo:
        sql += " AND (a.nome ILIKE %s OR a.numero_matricula ILIKE %s OR a.telefone ILIKE %s"
        termo_like = f"%{termo}%"
        parametros += [termo_like] * 3
        so_numeros = "".join(c for c in termo if c.isdigit())
        if so_numeros:
            sql += " OR a.cpf ILIKE %s"
            parametros.append(f"%{so_numeros}%")
        sql += ")"
    return buscar_todos(sql, tuple(parametros))

def listar_pagamentos_do_aluno(aluno_id):
    return buscar_todos(
        "SELECT id, mes_referencia, valor, data_pagamento, forma_pagamento, status FROM pagamentos WHERE aluno_id = %s",
        (aluno_id,)
    )

def buscar_pagamento(id):
    ''' Necessária nas rotas de editar e excluir.'''
    return buscar_um(
        "SELECT id, aluno_id, mes_referencia, valor, data_pagamento, forma_pagamento, status FROM pagamentos WHERE id = %s",
        (id,)
    )

def listar_status_pagamentos(mes_referencia, termo=""):
    '''Busca todos os alunos ativos e se ja pagaram o mes_referencia.
    p.id e p.valor vem None quando o aluno ainda nao pagou; nesse caso, a tela calcula
    se e pendente ou atrasado comparando hoje com dia_vencimento.
    a.mensalidade vem sempre, para somar o que falta receber.
    Com termo, so entram os alunos que combinam com a busca (nome, matricula, telefone ou CPF).'''
    sql = """SELECT a.id, a.nome, a.dia_vencimento, p.id, a.mensalidade, p.valor
             FROM alunos a
             LEFT JOIN pagamentos p ON p.aluno_id = a.id AND p.mes_referencia = %s
             WHERE a.status = 1
             AND substr(a.data_matricula, 1, 7) <= %s"""
    parametros = [mes_referencia, mes_referencia]
    if termo:
        sql += " AND (a.nome ILIKE %s OR a.numero_matricula ILIKE %s OR a.telefone ILIKE %s"
        termo_like = f"%{termo}%"
        parametros += [termo_like] * 3
        so_numeros = "".join(c for c in termo if c.isdigit())
        if so_numeros:
            sql += " OR a.cpf ILIKE %s"
            parametros.append(f"%{so_numeros}%")
        sql += ")"
    return buscar_todos(sql, tuple(parametros))

def listar_alunos_para_financeiro(termo=""):
    '''Alunos ativos com o que o financeiro precisa: id, nome, dia_vencimento, mensalidade e data_matricula.
    Com termo, so entram os alunos que combinam com a busca (nome, matricula, telefone ou CPF).'''
    sql = """SELECT a.id, a.nome, a.dia_vencimento, a.mensalidade, a.data_matricula
             FROM alunos a
             WHERE a.status = 1"""
    parametros = []
    if termo:
        sql += " AND (a.nome ILIKE %s OR a.numero_matricula ILIKE %s OR a.telefone ILIKE %s"
        termo_like = f"%{termo}%"
        parametros += [termo_like] * 3
        so_numeros = "".join(c for c in termo if c.isdigit())
        if so_numeros:
            sql += " OR a.cpf ILIKE %s"
            parametros.append(f"%{so_numeros}%")
        sql += ")"
    return buscar_todos(sql, tuple(parametros))

def listar_valores_pagos():
    '''Todos os pagamentos registrados: aluno_id, mes_referencia e valor.'''
    return buscar_todos("SELECT aluno_id, mes_referencia, valor FROM pagamentos")

def atualizar_pagamento(id, aluno_id, mes_referencia, valor, data_pagamento, forma_pagamento, status):
    return executar(
        "UPDATE pagamentos SET aluno_id = %s, mes_referencia = %s, valor = %s, data_pagamento = %s, forma_pagamento = %s, status = %s WHERE id = %s",
        (aluno_id, mes_referencia, valor, data_pagamento, forma_pagamento, status, id)
    )

def deletar_pagamento(id):
    return executar("DELETE FROM pagamentos WHERE id = %s", (id,))

###################
# Função usuários #
###################

def buscar_usuario(login):
    '''Busca um usuario pelo login, para usar em /login e conferir a senha com check_password_hash.
    Tupla: [0] id, [1] nome, [2] login, [3] senha_hash, [4] perfil. Devolve None se o login nao existir.'''
    return buscar_um(
        "SELECT id, nome, login, senha_hash, perfil FROM usuarios WHERE login = %s",
        (login,)
    )

def listar_usuarios():
    '''Lista todos os usuarios para a tela de gerenciamento (so o admin acessa).
    Tupla: [0] id, [1] nome, [2] login, [3] perfil. Nao traz a senha_hash.'''
    return buscar_todos(
        "SELECT id, nome, login, perfil FROM usuarios ORDER BY nome"
    )

def criar_usuario(nome, login, senha_hash, perfil):
    '''Cadastra um usuario novo. Recebe a senha ja transformada em hash (nunca a senha digitada).
    O login e UNIQUE: a rota deve conferir com buscar_usuario antes, para nao dar erro de duplicado.'''
    return executar(
        "INSERT INTO usuarios (nome, login, senha_hash, perfil) VALUES (%s, %s, %s, %s)",
        (nome, login, senha_hash, perfil)
    )

def atualizar_senha(login, senha_hash):
    '''Troca a senha de um usuario. Recebe a nova senha ja transformada em hash.'''
    return executar(
        "UPDATE usuarios SET senha_hash = %s WHERE login = %s",
        (senha_hash, login)
    )

def buscar_usuario_por_id(usuario_id):
    '''Busca um usuario pelo id, para as telas de excluir e redefinir senha.
    Tupla: [0] id, [1] nome, [2] login, [3] perfil. Devolve None se nao existir.'''
    return buscar_um(
        "SELECT id, nome, login, perfil FROM usuarios WHERE id = %s",
        (usuario_id,)
    )

def contar_administradores():
    '''Conta quantos usuarios tem perfil admin, para nao deixar remover o ultimo.'''
    return buscar_um(
        "SELECT COUNT(*) FROM usuarios WHERE perfil = 'admin'"
    )[0]

def excluir_usuario(usuario_id):
    '''Remove um usuario pelo id.'''
    return executar(
        "DELETE FROM usuarios WHERE id = %s",
        (usuario_id,)
    )

def atualizar_usuario(usuario_id, nome, login, perfil):
    '''Atualiza nome, login e perfil de um usuario. A senha tem funcao propria (atualizar_senha).'''
    return executar(
        "UPDATE usuarios SET nome = %s, login = %s, perfil = %s WHERE id = %s",
        (nome, login, perfil, usuario_id)
    )
