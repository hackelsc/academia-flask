import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, flash, session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
import funcoes_banco

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

CARGOS = [
    "Professor",
    "Personal trainer",
    "Instrutor de aulas coletivas",
    "Recepcionista",
    "Gerente",
    "Auxiliar de serviços gerais",
    "Fisioterapeuta",
    "Nutricionista",
    "Estagiário",
]

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]


def limpar_cpf(texto):
    return "".join(c for c in texto if c.isdigit())


def formatar_cpf(cpf):
    if not cpf or len(cpf) != 11:
        return cpf or ""
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def cpf_valido(cpf):
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[tamanho]):
            return False
    return True

FORMAS_PAGAMENTO = ["Dinheiro", "Pix", "Cartão de débito", "Cartão de crédito"]


def login_required(funcao):
    @wraps(funcao)
    def verificar_login(*args, **kwargs):
        if not session.get("usuario"):
            flash("Faça login para acessar esta página.")
            return redirect("/login")
        return funcao(*args, **kwargs)
    return verificar_login



def admin_required(funcao):
    @wraps(funcao)
    def verificar_admin(*args, **kwargs):
        if not session.get("usuario"):
            flash("Faça login para acessar esta página.")
            return redirect("/login")
        if session.get("perfil") != "admin":
            flash("Esta página é só para o administrador.")
            return redirect("/painel")
        return funcao(*args, **kwargs)
    return verificar_admin


@app.route("/")
def inicio():
    if session.get("usuario"):
        return redirect("/painel")
    return redirect("/login")


@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


@app.route("/contatos")
def contatos():
    return render_template("contatos.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    login_digitado = ""

    if request.method == "POST":
        login_digitado = request.form["login"].strip().lower()
        senha_digitada = request.form["senha"]

        usuario = funcoes_banco.buscar_usuario(login_digitado)

        if usuario is None or not check_password_hash(usuario[3], senha_digitada):
            erro = "Usuário ou senha inválidos."
        else:
            session["usuario"] = usuario[1]
            session["perfil"] = usuario[4]
            session["login"] = usuario[2]
            return redirect("/painel")

    return render_template("login.html", erro=erro, login_digitado=login_digitado)


@app.route("/painel")
@login_required
def painel():
    alunos_ativos = len(funcoes_banco.filtrar_alunos(status="1"))
    funcionarios_ativos = len(funcoes_banco.filtrar_funcionarios(status="1"))
    turmas_ativas = len(funcoes_banco.filtrar_turmas(status="1"))
    return render_template(
        "painel.html",
        alunos_ativos=alunos_ativos,
        funcionarios_ativos=funcionarios_ativos,
        turmas_ativas=turmas_ativas
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.")
    return redirect("/login")


@app.route("/usuarios", methods=["GET", "POST"])
@admin_required
def gerenciar_usuarios():
    erro = None

    if request.method == "POST":
        nome = request.form["nome"].strip()
        login = request.form["login"].strip().lower()
        senha = request.form["senha"]
        perfil = request.form["perfil"]

        if funcoes_banco.buscar_usuario(login):
            erro = "Já existe um usuário com este login."
        elif perfil not in ("admin", "recepcao"):
            erro = "Perfil inválido."
        else:
            senha_hash = generate_password_hash(senha)
            funcoes_banco.criar_usuario(nome, login, senha_hash, perfil)
            flash("Usuário cadastrado.")
            return redirect("/usuarios")

    lista_usuarios = funcoes_banco.listar_usuarios()
    return render_template("usuarios.html", usuarios=lista_usuarios, erro=erro)


@app.route("/senha", methods=["GET", "POST"])
@login_required
def trocar_senha():
    erro = None

    if request.method == "POST":
        senha_atual = request.form["senha_atual"]
        senha_nova = request.form["senha_nova"]
        senha_confirmacao = request.form["senha_confirmacao"]

        usuario = funcoes_banco.buscar_usuario(session["login"])

        if not check_password_hash(usuario[3], senha_atual):
            erro = "A senha atual está incorreta."
        elif senha_nova != senha_confirmacao:
            erro = "A nova senha e a confirmação são diferentes."
        elif len(senha_nova) < 8:
            erro = "A nova senha deve ter pelo menos 8 caracteres."
        else:
            senha_hash = generate_password_hash(senha_nova)
            funcoes_banco.atualizar_senha(session["login"], senha_hash)
            flash("Senha alterada com sucesso.")
            return redirect("/painel")

    return render_template("senha.html", erro=erro)


@app.route("/usuarios/<int:id>/excluir", methods=["GET", "POST"])
@admin_required
def usuarios_excluir(id):
    usuario = funcoes_banco.buscar_usuario_por_id(id)
    if usuario is None:
        flash("Usuário não encontrado.")
        return redirect("/usuarios")

    if usuario[2] == session["login"]:
        flash("Você não pode excluir o seu próprio usuário.")
        return redirect("/usuarios")

    if usuario[3] == "admin" and funcoes_banco.contar_administradores() <= 1:
        flash("Não é possível excluir o último administrador.")
        return redirect("/usuarios")

    if request.method == "POST":
        funcoes_banco.excluir_usuario(id)
        flash(f"Usuário \"{usuario[1]}\" excluído com sucesso!")
        return redirect("/usuarios")

    return render_template("excluir_usuario.html", id=id, nome=usuario[1], login=usuario[2])


@app.route("/usuarios/<int:id>/editar", methods=["GET", "POST"])
@admin_required
def usuarios_editar(id):
    usuario = funcoes_banco.buscar_usuario_por_id(id)
    if usuario is None:
        flash("Usuário não encontrado.")
        return redirect("/usuarios")

    erro = None
    nome = usuario[1]
    login = usuario[2]
    perfil = usuario[3]

    if request.method == "POST":
        nome = request.form["nome"].strip()
        login = request.form["login"].strip().lower()
        perfil = request.form["perfil"]
        senha_nova = request.form["senha_nova"]
        senha_confirmacao = request.form["senha_confirmacao"]

        usuario_com_login = funcoes_banco.buscar_usuario(login)

        if usuario_com_login and usuario_com_login[0] != id:
            erro = "Já existe outro usuário com este login."
        elif perfil not in ("admin", "recepcao"):
            erro = "Perfil inválido."
        elif usuario[3] == "admin" and perfil != "admin" and funcoes_banco.contar_administradores() <= 1:
            erro = "Não é possível rebaixar o último administrador."
        elif senha_nova != senha_confirmacao:
            erro = "A senha e a confirmação são diferentes."
        elif senha_nova and len(senha_nova) < 8:
            erro = "A senha deve ter pelo menos 8 caracteres."
        else:
            funcoes_banco.atualizar_usuario(id, nome, login, perfil)
            if senha_nova:
                senha_hash = generate_password_hash(senha_nova)
                funcoes_banco.atualizar_senha(login, senha_hash)
            if usuario[2] == session["login"]:
                session["usuario"] = nome
                session["login"] = login
                session["perfil"] = perfil
            flash(f"Usuário \"{nome}\" atualizado com sucesso!")
            return redirect("/usuarios")

    return render_template("editar_usuario.html", id=id, nome=nome, login=login, perfil=perfil, erro=erro)


@app.route("/alunos")
@login_required
def alunos_pagina():
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "1")
    lista_alunos = funcoes_banco.filtrar_alunos(busca, status)
    return render_template("alunos.html", alunos=lista_alunos, total=len(lista_alunos), busca=busca, status=status)


@app.route("/alunos/novo", methods=["GET", "POST"])
@login_required
def alunos_novo():
    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        rua = request.form["rua"]
        numero = request.form["numero"]
        complemento = request.form["complemento"]
        bairro = request.form["bairro"]
        cidade = request.form["cidade"]
        uf = request.form["uf"]
        cep = request.form["cep"]
        nascimento = request.form["nascimento"]
        mensalidade = request.form["mensalidade"]
        dia_vencimento = request.form["dia_vencimento"]

        erro = None
        cpf_numeros = limpar_cpf(cpf)
        aluno_com_cpf = funcoes_banco.buscar_aluno_por_cpf(cpf_numeros) if cpf_numeros else None

        if not nome.strip():
            erro = "O nome é obrigatório."
        elif not telefone.strip():
            erro = "O telefone é obrigatório."
        elif cpf.strip() and not cpf_valido(cpf_numeros):
            erro = "CPF inválido."
        elif aluno_com_cpf:
            erro = "Já existe um aluno com este CPF."
        elif not mensalidade.strip():
            erro = "A mensalidade é obrigatória."
        elif not dia_vencimento.strip():
            erro = "O dia de vencimento é obrigatório."
        else:
            try:
                mensalidade = float(mensalidade)
                dia_vencimento = int(dia_vencimento)
                if mensalidade < 0:
                    erro = "A mensalidade não pode ser negativa."
                elif dia_vencimento < 1 or dia_vencimento > 31:
                    erro = "O dia de vencimento deve estar entre 1 e 31."
            except ValueError:
                erro = "Mensalidade e dia de vencimento devem ser números."

        if erro:
            return render_template(
                "cadastro_alunos.html",
                erro=erro,
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                email=email,
                rua=rua,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                cidade=cidade,
                uf=uf,
                cep=cep,
                nascimento=nascimento,
                mensalidade=request.form["mensalidade"],
                dia_vencimento=request.form["dia_vencimento"],
            )

        funcoes_banco.cadastrar_aluno(
            nome, cpf_numeros or None, telefone, email, rua, numero, complemento,
            bairro, cidade, uf, cep, nascimento,
            mensalidade, dia_vencimento, 1
        )
        flash(f"Aluno \"{nome}\" cadastrado com sucesso!")
        return redirect("/alunos")

    return render_template("cadastro_alunos.html")



@app.route("/alunos/<int:id>/editar", methods=["GET", "POST"])
@login_required
def alunos_editar(id):
    aluno = funcoes_banco.buscar_aluno(id)
    if aluno is None:
        flash("Aluno não encontrado.")
        return redirect("/alunos")

    erro = None
    nome = aluno[2]
    cpf = formatar_cpf(aluno[3])
    telefone = aluno[4]
    email = aluno[5]
    rua = aluno[6]
    numero = aluno[7]
    complemento = aluno[8]
    bairro = aluno[9]
    cidade = aluno[10]
    uf = aluno[11]
    cep = aluno[12]
    nascimento = aluno[13]
    mensalidade = aluno[14]
    dia_vencimento = aluno[15]

    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        rua = request.form["rua"]
        numero = request.form["numero"]
        complemento = request.form["complemento"]
        bairro = request.form["bairro"]
        cidade = request.form["cidade"]
        uf = request.form["uf"]
        cep = request.form["cep"]
        nascimento = request.form["nascimento"]
        mensalidade = request.form["mensalidade"]
        dia_vencimento = request.form["dia_vencimento"]

        cpf_numeros = limpar_cpf(cpf)
        aluno_com_cpf = funcoes_banco.buscar_aluno_por_cpf(cpf_numeros) if cpf_numeros else None

        if not nome.strip():
            erro = "O nome é obrigatório."
        elif not telefone.strip():
            erro = "O telefone é obrigatório."
        elif cpf.strip() and not cpf_valido(cpf_numeros):
            erro = "CPF inválido."
        elif aluno_com_cpf and aluno_com_cpf[0] != id:
            erro = "Já existe outro aluno com este CPF."
        elif not mensalidade.strip():
            erro = "A mensalidade é obrigatória."
        elif not dia_vencimento.strip():
            erro = "O dia de vencimento é obrigatório."
        else:
            try:
                mensalidade = float(mensalidade)
                dia_vencimento = int(dia_vencimento)
                if mensalidade < 0:
                    erro = "A mensalidade não pode ser negativa."
                elif dia_vencimento < 1 or dia_vencimento > 31:
                    erro = "O dia de vencimento deve estar entre 1 e 31."
            except ValueError:
                erro = "Mensalidade e dia de vencimento devem ser números."

        if not erro:
            funcoes_banco.atualizar_aluno(
                aluno[1], nome, cpf_numeros or None, telefone, email, rua, numero, complemento,
                bairro, cidade, uf, cep, nascimento,
                mensalidade, dia_vencimento, aluno[16], aluno[17], id
            )
            flash(f"Aluno \"{nome}\" atualizado com sucesso!")
            return redirect("/alunos")

    return render_template(
        "editar_aluno.html",
        erro=erro,
        id=id,
        matricula=aluno[1],
        nome=nome,
        cpf=cpf,
        telefone=telefone,
        email=email,
        rua=rua,
        numero=numero,
        complemento=complemento,
        bairro=bairro,
        cidade=cidade,
        uf=uf,
        cep=cep,
        nascimento=nascimento,
        mensalidade=mensalidade,
        dia_vencimento=dia_vencimento,
    )


@app.route("/alunos/<int:id>/inativar", methods=["POST"])
@login_required
def alunos_inativar(id):
    aluno = funcoes_banco.buscar_aluno(id)
    if aluno is None:
        flash("Aluno não encontrado.")
        return redirect("/alunos")

    funcoes_banco.inativar_aluno(id)
    flash(f"Aluno \"{aluno[2]}\" inativado com sucesso!")
    return redirect("/alunos")


@app.route("/alunos/<int:id>/reativar", methods=["POST"])
@login_required
def alunos_reativar(id):
    aluno = funcoes_banco.buscar_aluno(id)
    if aluno is None:
        flash("Aluno não encontrado.")
        return redirect("/alunos")

    funcoes_banco.reativar_aluno(id)
    flash(f"Aluno \"{aluno[2]}\" reativado com sucesso!")
    return redirect("/alunos")


@app.route("/alunos/<int:id>/turmas")
@login_required
def alunos_turmas(id):
    aluno = funcoes_banco.buscar_aluno(id)
    if aluno is None:
        flash("Aluno não encontrado.")
        return redirect("/alunos")

    turmas = funcoes_banco.listar_turmas_por_aluno(id)

    ids_turmas_matriculadas = []
    for turma in turmas:
        ids_turmas_matriculadas.append(turma[1])

    turmas_disponiveis = []
    for turma in funcoes_banco.filtrar_turmas("", "", "", "1"):
        if turma[0] not in ids_turmas_matriculadas:
            turmas_disponiveis.append(turma)

    return render_template(
        "aluno_turmas.html",
        id=id,
        numero_matricula=aluno[1],
        nome=aluno[2],
        status=aluno[17],
        turmas=turmas,
        total=len(turmas),
        turmas_disponiveis=turmas_disponiveis,
    )


@app.route("/alunos/<int:id>/turmas/matricular", methods=["POST"])
@login_required
def alunos_matricular(id):
    aluno = funcoes_banco.buscar_aluno(id)
    if aluno is None:
        flash("Aluno não encontrado.")
        return redirect("/alunos")

    if aluno[17] != 1:
        flash("Não é possível matricular um aluno inativo.")
        return redirect(f"/alunos/{id}/turmas")

    turma_id = request.form["turma_id"]
    if not turma_id.isdigit():
        flash("Escolha uma turma.")
        return redirect(f"/alunos/{id}/turmas")

    turma = funcoes_banco.buscar_turma(int(turma_id))
    if turma is None or turma[6] != 1:
        flash("Turma não encontrada ou inativa.")
        return redirect(f"/alunos/{id}/turmas")

    for matricula in funcoes_banco.listar_turmas_por_aluno(id):
        if matricula[1] == turma[0]:
            flash("Esse aluno já está matriculado nessa turma.")
            return redirect(f"/alunos/{id}/turmas")

    funcoes_banco.matricular_aluno(turma[0], id)
    flash(f"Aluno \"{aluno[2]}\" matriculado com sucesso!")
    return redirect(f"/alunos/{id}/turmas")


@app.route("/alunos/<int:id>/turmas/<int:matricula_id>/desmatricular", methods=["POST"])
@login_required
def alunos_desmatricular(id, matricula_id):
    for matricula in funcoes_banco.listar_turmas_por_aluno(id):
        if matricula[0] == matricula_id:
            funcoes_banco.desmatricular_aluno(matricula_id)
            flash("Aluno desmatriculado da turma com sucesso!")
            return redirect(f"/alunos/{id}/turmas")

    flash("Matrícula não encontrada para este aluno.")
    return redirect(f"/alunos/{id}/turmas")

@app.route("/alunos/<int:id>/pagamentos", methods=["GET", "POST"])
@login_required
def alunos_pagamentos(id):
    aluno = funcoes_banco.buscar_aluno(id)
    if aluno is None:
        flash("Aluno não encontrado.")
        return redirect("/alunos")

    erro = None
    mes_referencia = date.today().strftime("%Y-%m")
    valor = f"{aluno[14]:.2f}"
    forma_pagamento = ""

    if request.method == "POST":
        mes_referencia = request.form["mes_referencia"]
        valor = request.form["valor"]
        forma_pagamento = request.form["forma_pagamento"]

        if aluno[17] != 1:
            erro = "Não é possível registrar pagamento de um aluno inativo."
        elif not mes_referencia.strip():
            erro = "O mês de referência é obrigatório."
        elif forma_pagamento not in FORMAS_PAGAMENTO:
            erro = "Escolha uma forma de pagamento da lista."
        else:
            try:
                valor_numero = float(valor)
                if valor_numero <= 0:
                    erro = "O valor deve ser maior que zero."
            except ValueError:
                erro = "O valor deve ser um número."

        if not erro:
            for pagamento in funcoes_banco.listar_pagamentos_do_aluno(id):
                if pagamento[1] == mes_referencia:
                    erro = "Esse aluno já tem um pagamento registrado para esse mês."

        if not erro:
            funcoes_banco.registrar_pagamento(id, mes_referencia, valor_numero, forma_pagamento)
            flash("Pagamento registrado com sucesso!")
            return redirect(f"/alunos/{id}/pagamentos")

    pagamentos = funcoes_banco.listar_pagamentos_do_aluno(id)

    return render_template(
        "aluno_pagamentos.html",
        id=id,
        numero_matricula=aluno[1],
        nome=aluno[2],
        mensalidade=aluno[14],
        dia_vencimento=aluno[15],
        status=aluno[17],
        pagamentos=pagamentos,
        total=len(pagamentos),
        erro=erro,
        formas_pagamento=FORMAS_PAGAMENTO,
        mes_referencia=mes_referencia,
        valor=valor,
        forma_pagamento=forma_pagamento,
    )


@app.route("/alunos/<int:id>/pagamentos/<int:pagamento_id>/editar", methods=["GET", "POST"])
@login_required
def alunos_pagamentos_editar(id, pagamento_id):
    aluno = funcoes_banco.buscar_aluno(id)
    if aluno is None:
        flash("Aluno não encontrado.")
        return redirect("/alunos")

    pagamento = funcoes_banco.buscar_pagamento(pagamento_id)
    if pagamento is None or pagamento[1] != id:
        flash("Pagamento não encontrado.")
        return redirect(f"/alunos/{id}/pagamentos")

    erro = None
    mes_referencia = pagamento[2]
    valor = f"{pagamento[3]:.2f}"
    forma_pagamento = pagamento[5]

    if request.method == "POST":
        mes_referencia = request.form["mes_referencia"]
        valor = request.form["valor"]
        forma_pagamento = request.form["forma_pagamento"]

        if not mes_referencia.strip():
            erro = "O mês de referência é obrigatório."
        elif forma_pagamento not in FORMAS_PAGAMENTO:
            erro = "Escolha uma forma de pagamento da lista."
        else:
            try:
                valor_numero = float(valor)
                if valor_numero <= 0:
                    erro = "O valor deve ser maior que zero."
            except ValueError:
                erro = "O valor deve ser um número."

        if not erro:
            for outro_pagamento in funcoes_banco.listar_pagamentos_do_aluno(id):
                if outro_pagamento[1] == mes_referencia and outro_pagamento[0] != pagamento_id:
                    erro = "Esse aluno já tem um pagamento registrado para esse mês."

        if not erro:
            funcoes_banco.atualizar_pagamento(pagamento_id, id, mes_referencia, valor_numero, pagamento[4], forma_pagamento, pagamento[6])
            flash("Pagamento atualizado com sucesso!")
            return redirect(f"/alunos/{id}/pagamentos")

    return render_template(
        "editar_pagamento.html",
        id=id,
        pagamento_id=pagamento_id,
        nome=aluno[2],
        erro=erro,
        formas_pagamento=FORMAS_PAGAMENTO,
        mes_referencia=mes_referencia,
        valor=valor,
        forma_pagamento=forma_pagamento,
    )


@app.route("/alunos/<int:id>/pagamentos/<int:pagamento_id>/excluir", methods=["GET", "POST"])
@login_required
def alunos_pagamentos_excluir(id, pagamento_id):
    aluno = funcoes_banco.buscar_aluno(id)
    if aluno is None:
        flash("Aluno não encontrado.")
        return redirect("/alunos")

    pagamento = funcoes_banco.buscar_pagamento(pagamento_id)
    if pagamento is None or pagamento[1] != id:
        flash("Pagamento não encontrado.")
        return redirect(f"/alunos/{id}/pagamentos")

    if request.method == "POST":
        funcoes_banco.deletar_pagamento(pagamento_id)
        flash("Pagamento excluído com sucesso!")
        return redirect(f"/alunos/{id}/pagamentos")

    return render_template(
        "excluir_pagamento.html",
        id=id,
        pagamento_id=pagamento_id,
        nome=aluno[2],
        mes_referencia=pagamento[2],
        valor=pagamento[3],
        forma_pagamento=pagamento[5],
    )


@app.route("/funcionarios")
@login_required
def funcionarios_pagina():
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "1")
    cargo = request.args.get("cargo", "")
    lista_funcionarios = funcoes_banco.filtrar_funcionarios(busca, status, cargo)
    return render_template(
        "funcionarios.html",
        funcionarios=lista_funcionarios,
        total=len(lista_funcionarios),
        busca=busca,
        status=status,
        cargo=cargo,
        cargos=CARGOS,
    )


@app.route("/funcionarios/novo", methods=["GET", "POST"])
@login_required
def funcionarios_novo():
    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        cargo = request.form["cargo"]
        rua = request.form["rua"]
        numero = request.form["numero"]
        complemento = request.form["complemento"]
        bairro = request.form["bairro"]
        cidade = request.form["cidade"]
        uf = request.form["uf"]
        cep = request.form["cep"]
        data_nascimento = request.form["data_nascimento"]
        data_admissao = request.form["data_admissao"]

        erro = None
        cpf_numeros = limpar_cpf(cpf)
        funcionario_com_cpf = funcoes_banco.buscar_funcionario_por_cpf(cpf_numeros) if cpf_numeros else None

        if not nome.strip():
            erro = "O nome é obrigatório."
        elif not telefone.strip():
            erro = "O telefone é obrigatório."
        elif cpf.strip() and not cpf_valido(cpf_numeros):
            erro = "CPF inválido."
        elif funcionario_com_cpf:
            erro = "Já existe um funcionário com este CPF."
        elif cargo not in CARGOS:
            erro = "Escolha um cargo da lista."
        elif not data_admissao.strip():
            erro = "A data de admissão é obrigatória."

        if erro:
            return render_template(
                "cadastro_funcionarios.html",
                erro=erro,
                cargos=CARGOS,
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                email=email,
                cargo=cargo,
                rua=rua,
                numero=numero,
                complemento=complemento,
                bairro=bairro,
                cidade=cidade,
                uf=uf,
                cep=cep,
                data_nascimento=data_nascimento,
                data_admissao=data_admissao,
            )

        funcoes_banco.cadastrar_funcionario(
            nome, cpf_numeros or None, telefone, email, cargo, rua, numero, complemento,
            bairro, cidade, uf, cep, data_nascimento, data_admissao, 1
        )
        flash(f"Funcionário \"{nome}\" cadastrado com sucesso!")
        return redirect("/funcionarios")

    return render_template("cadastro_funcionarios.html", cargos=CARGOS)


@app.route("/funcionarios/<int:id>/editar", methods=["GET", "POST"])
@login_required
def funcionarios_editar(id):
    funcionario = funcoes_banco.buscar_funcionario(id)
    if funcionario is None:
        flash("Funcionário não encontrado.")
        return redirect("/funcionarios")

    erro = None
    nome = funcionario[1]
    cpf = formatar_cpf(funcionario[2])
    telefone = funcionario[3]
    email = funcionario[4]
    cargo = funcionario[5]
    rua = funcionario[6]
    numero = funcionario[7]
    complemento = funcionario[8]
    bairro = funcionario[9]
    cidade = funcionario[10]
    uf = funcionario[11]
    cep = funcionario[12]
    data_nascimento = funcionario[13]
    data_admissao = funcionario[14]

    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        telefone = request.form["telefone"]
        email = request.form["email"]
        cargo = request.form["cargo"]
        rua = request.form["rua"]
        numero = request.form["numero"]
        complemento = request.form["complemento"]
        bairro = request.form["bairro"]
        cidade = request.form["cidade"]
        uf = request.form["uf"]
        cep = request.form["cep"]
        data_nascimento = request.form["data_nascimento"]
        data_admissao = request.form["data_admissao"]

        cpf_numeros = limpar_cpf(cpf)
        funcionario_com_cpf = funcoes_banco.buscar_funcionario_por_cpf(cpf_numeros) if cpf_numeros else None

        if not nome.strip():
            erro = "O nome é obrigatório."
        elif not telefone.strip():
            erro = "O telefone é obrigatório."
        elif cpf.strip() and not cpf_valido(cpf_numeros):
            erro = "CPF inválido."
        elif funcionario_com_cpf and funcionario_com_cpf[0] != id:
            erro = "Já existe outro funcionário com este CPF."
        elif cargo not in CARGOS:
            erro = "Escolha um cargo da lista."
        elif not data_admissao.strip():
            erro = "A data de admissão é obrigatória."

        if not erro:
            funcoes_banco.atualizar_funcionario(
                nome, cpf_numeros or None, telefone, email, cargo, rua, numero, complemento,
                bairro, cidade, uf, cep, data_nascimento, data_admissao,
                funcionario[15], id
            )
            flash(f"Funcionário \"{nome}\" atualizado com sucesso!")
            return redirect("/funcionarios")

    return render_template(
        "editar_funcionario.html",
        erro=erro,
        id=id,
        cargos=CARGOS,
        nome=nome,
        cpf=cpf,
        telefone=telefone,
        email=email,
        cargo=cargo,
        rua=rua,
        numero=numero,
        complemento=complemento,
        bairro=bairro,
        cidade=cidade,
        uf=uf,
        cep=cep,
        data_nascimento=data_nascimento,
        data_admissao=data_admissao,
    )


@app.route("/funcionarios/<int:id>/inativar", methods=["POST"])
@login_required
def funcionarios_inativar(id):
    funcionario = funcoes_banco.buscar_funcionario(id)
    if funcionario is None:
        flash("Funcionário não encontrado.")
        return redirect("/funcionarios")

    funcoes_banco.inativar_funcionario(id)
    flash(f"Funcionário \"{funcionario[1]}\" inativado com sucesso!")
    return redirect("/funcionarios")


@app.route("/funcionarios/<int:id>/reativar", methods=["POST"])
@login_required
def funcionarios_reativar(id):
    funcionario = funcoes_banco.buscar_funcionario(id)
    if funcionario is None:
        flash("Funcionário não encontrado.")
        return redirect("/funcionarios")

    funcoes_banco.reativar_funcionario(id)
    flash(f"Funcionário \"{funcionario[1]}\" reativado com sucesso!")
    return redirect("/funcionarios")


@app.route("/modalidades", methods=["GET", "POST"])
@login_required
def modalidades_pagina():
    erro = None
    nome = ""

    if request.method == "POST":
        nome = request.form["nome"].strip()
        nomes_existentes = [m[1].lower() for m in funcoes_banco.listar_modalidades()]

        if not nome:
            erro = "O nome da modalidade é obrigatório."
        elif nome.lower() in nomes_existentes:
            erro = "Essa modalidade já está cadastrada."
        else:
            funcoes_banco.cadastrar_modalidade(nome)
            flash(f"Modalidade \"{nome}\" cadastrada com sucesso!")
            return redirect("/modalidades")

    lista_modalidades = funcoes_banco.listar_modalidades()
    return render_template(
        "modalidades.html",
        modalidades=lista_modalidades,
        total=len(lista_modalidades),
        erro=erro,
        nome=nome,
    )


@app.route("/modalidades/<int:id>/editar", methods=["GET", "POST"])
@login_required
def modalidades_editar(id):
    modalidade = funcoes_banco.buscar_modalidade(id)
    if modalidade is None:
        flash("Modalidade não encontrada.")
        return redirect("/modalidades")

    erro = None
    nome = modalidade[1]

    if request.method == "POST":
        nome = request.form["nome"].strip()
        outros_nomes = [m[1].lower() for m in funcoes_banco.listar_modalidades() if m[0] != id]

        if not nome:
            erro = "O nome da modalidade é obrigatório."
        elif nome.lower() in outros_nomes:
            erro = "Essa modalidade já está cadastrada."
        else:
            funcoes_banco.atualizar_modalidade(id, nome)
            flash(f"Modalidade \"{nome}\" atualizada com sucesso!")
            return redirect("/modalidades")

    return render_template("editar_modalidade.html", erro=erro, id=id, nome=nome)


@app.route("/modalidades/<int:id>/excluir", methods=["GET", "POST"])
@login_required
def modalidades_excluir(id):
    modalidade = funcoes_banco.buscar_modalidade(id)
    if modalidade is None:
        flash("Modalidade não encontrada.")
        return redirect("/modalidades")

    turmas = funcoes_banco.listar_turmas_por_modalidade(id)
    if turmas:
        flash(f"Não é possível excluir \"{modalidade[1]}\": há {len(turmas)} turma(s) usando essa modalidade.")
        return redirect("/modalidades")

    if request.method == "POST":
        funcoes_banco.deletar_modalidade(id)
        flash(f"Modalidade \"{modalidade[1]}\" excluída com sucesso!")
        return redirect("/modalidades")

    return render_template("excluir_modalidade.html", id=id, nome=modalidade[1])


@app.route("/turmas")
@login_required
def turmas_pagina():
    modalidade_id = request.args.get("modalidade_id", "")
    funcionario_id = request.args.get("funcionario_id", "")
    dia_semana = request.args.get("dia_semana", "")
    status = request.args.get("status", "1")
    turmas = funcoes_banco.filtrar_turmas(modalidade_id, funcionario_id, dia_semana, status)
    return render_template(
        "turmas.html",
        turmas=turmas,
        total=len(turmas),
        modalidades=funcoes_banco.listar_modalidades(),
        professores=funcoes_banco.listar_funcionarios(),
        dias_semana=DIAS_SEMANA,
        modalidade_id=modalidade_id,
        funcionario_id=funcionario_id,
        dia_semana=dia_semana,
        status=status,
    )


@app.route("/turmas/novo", methods=["GET", "POST"])
@login_required
def turmas_novo():
    modalidades = funcoes_banco.listar_modalidades()
    professores = funcoes_banco.filtrar_funcionarios("", "1", "")

    if request.method == "POST":
        modalidade_id = request.form["modalidade_id"]
        funcionario_id = request.form["funcionario_id"]
        dias_marcados = request.form.getlist("dia_semana")
        dia_semana = ", ".join(dias_marcados)
        horario_inicio = request.form["horario_inicio"]
        horario_fim = request.form["horario_fim"]

        erro = None

        try:
            modalidade_id_numero = int(modalidade_id)
            funcionario_id_numero = int(funcionario_id) if funcionario_id else None
        except ValueError:
            erro = "Escolha uma modalidade."

        if erro:
            pass
        elif not dias_marcados or any(d not in DIAS_SEMANA for d in dias_marcados):
            erro = "Marque pelo menos um dia da semana."
        elif not horario_inicio or not horario_fim:
            erro = "Os horários de início e de fim são obrigatórios."
        elif horario_fim <= horario_inicio:
            erro = "O horário de fim deve ser depois do horário de início."

        if erro:
            return render_template(
                "cadastro_turmas.html",
                erro=erro,
                modalidades=modalidades,
                professores=professores,
                dias_semana=DIAS_SEMANA,
                modalidade_id=modalidade_id,
                funcionario_id=funcionario_id,
                dia_semana=dia_semana,
                horario_inicio=horario_inicio,
                horario_fim=horario_fim,
            )

        funcoes_banco.cadastrar_turma(
            modalidade_id_numero, funcionario_id_numero, dia_semana,
            horario_inicio, horario_fim, 1
        )
        flash("Turma cadastrada com sucesso!")
        return redirect("/turmas")

    return render_template(
        "cadastro_turmas.html",
        modalidades=modalidades,
        professores=professores,
        dias_semana=DIAS_SEMANA,
    )


@app.route("/turmas/<int:id>/editar", methods=["GET", "POST"])
@login_required
def turmas_editar(id):
    turma = funcoes_banco.buscar_turma(id)
    if turma is None:
        flash("Turma não encontrada.")
        return redirect("/turmas")

    modalidades = funcoes_banco.listar_modalidades()
    professores = funcoes_banco.filtrar_funcionarios("", "1", "")

    erro = None
    modalidade_id = str(turma[1])
    funcionario_id = str(turma[2])
    dia_semana = turma[3]
    horario_inicio = turma[4]
    horario_fim = turma[5]

    if request.method == "POST":
        modalidade_id = request.form["modalidade_id"]
        funcionario_id = request.form["funcionario_id"]
        dias_marcados = request.form.getlist("dia_semana")
        dia_semana = ", ".join(dias_marcados)
        horario_inicio = request.form["horario_inicio"]
        horario_fim = request.form["horario_fim"]

        try:
            modalidade_id_numero = int(modalidade_id)
            funcionario_id_numero = int(funcionario_id) if funcionario_id else None
        except ValueError:
            erro = "Escolha uma modalidade."

        if erro:
            pass
        elif not dias_marcados or any(d not in DIAS_SEMANA for d in dias_marcados):
            erro = "Marque pelo menos um dia da semana."
        elif not horario_inicio or not horario_fim:
            erro = "Os horários de início e de fim são obrigatórios."
        elif horario_fim <= horario_inicio:
            erro = "O horário de fim deve ser depois do horário de início."

        if not erro:
            funcoes_banco.atualizar_turma(
                id, modalidade_id_numero, funcionario_id_numero, dia_semana,
                horario_inicio, horario_fim, turma[6]
            )
            flash("Turma atualizada com sucesso!")
            return redirect("/turmas")

    return render_template(
        "editar_turma.html",
        id=id,
        erro=erro,
        modalidades=modalidades,
        professores=professores,
        dias_semana=DIAS_SEMANA,
        modalidade_id=modalidade_id,
        funcionario_id=funcionario_id,
        dia_semana=dia_semana,
        horario_inicio=horario_inicio,
        horario_fim=horario_fim,
    )


@app.route("/turmas/<int:id>/inativar", methods=["POST"])
@login_required
def turmas_inativar(id):
    turma = funcoes_banco.buscar_turma(id)
    if turma is None:
        flash("Turma não encontrada.")
        return redirect("/turmas")

    funcoes_banco.inativar_turma(id)
    flash("Turma inativada com sucesso!")
    return redirect("/turmas")


@app.route("/turmas/<int:id>/reativar", methods=["POST"])
@login_required
def turmas_reativar(id):
    turma = funcoes_banco.buscar_turma(id)
    if turma is None:
        flash("Turma não encontrada.")
        return redirect("/turmas")

    funcoes_banco.reativar_turma(id)
    flash("Turma reativada com sucesso!")
    return redirect("/turmas")

@app.route("/turmas/<int:id>/excluir", methods=["GET", "POST"])
@login_required
def turmas_excluir(id):
    turma = funcoes_banco.buscar_turma(id)
    if turma is None:
        flash("Turma não encontrada.")
        return redirect("/turmas")

    alunos = funcoes_banco.listar_alunos_por_turma(id)
    if alunos:
        flash(f"Não é possível excluir a turma: há {len(alunos)} aluno(s) matriculado(s). Inative a turma ou desmatricule os alunos antes.")
        return redirect("/turmas")

    if request.method == "POST":
        funcoes_banco.deletar_turma(id)
        flash("Turma excluída com sucesso!")
        return redirect("/turmas")

    modalidade = funcoes_banco.buscar_modalidade(turma[1])
    professor = funcoes_banco.buscar_funcionario(turma[2]) if turma[2] else None
    return render_template(
        "excluir_turma.html",
        id=id,
        modalidade=modalidade[1],
        professor=professor[1] if professor else "Sem professor fixo",
        dia_semana=turma[3],
        horario_inicio=turma[4],
        horario_fim=turma[5],
    )


@app.route("/turmas/<int:id>/alunos")
@login_required
def turmas_alunos(id):
    turma = funcoes_banco.buscar_turma(id)
    if turma is None:
        flash("Turma não encontrada.")
        return redirect("/turmas")

    modalidade = funcoes_banco.buscar_modalidade(turma[1])
    professor = funcoes_banco.buscar_funcionario(turma[2]) if turma[2] else None
    alunos = funcoes_banco.listar_alunos_por_turma(id)

    return render_template(
        "turma_alunos.html",
        id=id,
        modalidade=modalidade[1],
        professor=professor[1] if professor else "Sem professor fixo",
        dia_semana=turma[3],
        horario_inicio=turma[4],
        horario_fim=turma[5],
        status=turma[6],
        alunos=alunos,
        total=len(alunos),
    )


@app.route("/turmas/<int:id>/alunos/<int:matricula_id>/desmatricular", methods=["POST"])
@login_required
def turmas_desmatricular(id, matricula_id):
    for matriculado in funcoes_banco.listar_alunos_por_turma(id):
        if matriculado[0] == matricula_id:
            funcoes_banco.desmatricular_aluno(matricula_id)
            flash(f"Aluno \"{matriculado[3]}\" desmatriculado com sucesso!")
            return redirect(f"/turmas/{id}/alunos")

    flash("Matrícula não encontrada nesta turma.")
    return redirect(f"/turmas/{id}/alunos")

@app.route("/financeiro/historico")
@login_required
def financeiro_historico():
    busca = request.args.get("busca", "").strip()
    pagamentos = funcoes_banco.listar_pagamentos(busca)
    total = len(pagamentos)
    return render_template("pagamentos.html", pagamentos=pagamentos, total=total, busca=busca)

LIMITE_LINHAS = 300

def calcular_situacao(mes, mes_atual, dia_vencimento, pago, hoje):
    if pago:
        return "Pago"
    if mes < mes_atual:
        return "Atrasado"
    if mes == mes_atual and hoje.day > dia_vencimento:
        return "Atrasado"
    return "Pendente"

def listar_meses(inicio, fim):
    '''Devolve os meses no formato AAAA-MM, de inicio ate fim (inclusive).'''
    meses = []
    ano = int(inicio[:4])
    mes = int(inicio[5:7])
    while f"{ano:04d}-{mes:02d}" <= fim:
        meses.append(f"{ano:04d}-{mes:02d}")
        mes += 1
        if mes == 13:
            ano += 1
            mes = 1
    return meses

@app.route("/financeiro")
@login_required
def financeiro_pagina():
    hoje = date.today()
    mes_atual = hoje.strftime("%Y-%m")

    mes = request.args.get("mes", "").strip()
    if len(mes) != 7 or mes[4] != "-":
        mes = mes_atual

    busca = request.args.get("busca", "").strip()
    filtro_situacao = request.args.get("situacao", "").strip()
    if filtro_situacao not in ("Pago", "Pendente", "Atrasado"):
        filtro_situacao = ""
    todos_meses = request.args.get("todos") == "1"

    ids_da_busca = {a[0] for a in funcoes_banco.listar_alunos_para_financeiro(busca)}

    linhas = []
    if todos_meses:
        valores_pagos = {}
        for pagamento in funcoes_banco.listar_valores_pagos():
            valores_pagos[(pagamento[0], pagamento[1])] = pagamento[2]
        for aluno in funcoes_banco.listar_alunos_para_financeiro():
            for mes_da_linha in listar_meses(aluno[4][:7], mes_atual):
                valor_pago = valores_pagos.get((aluno[0], mes_da_linha))
                linhas.append((aluno[0], aluno[1], aluno[2], aluno[3], mes_da_linha, valor_pago))
        linhas.sort(key=lambda linha: (linha[4], linha[1]))
    else:
        for aluno_e_pagamento in funcoes_banco.listar_status_pagamentos(mes):
            linhas.append((aluno_e_pagamento[0], aluno_e_pagamento[1], aluno_e_pagamento[2], aluno_e_pagamento[4], mes, aluno_e_pagamento[5]))

    situacoes = []
    total_pago = 0
    total_pendente = 0
    total_atrasado = 0
    valor_recebido = 0
    valor_a_receber = 0
    valor_em_atraso = 0

    for id_aluno, nome_aluno, dia_vencimento, mensalidade, mes_da_linha, valor_pago in linhas:
        situacao = calcular_situacao(mes_da_linha, mes_atual, dia_vencimento, valor_pago is not None, hoje)

        if situacao == "Pago":
            total_pago += 1
            valor_recebido += valor_pago
        elif situacao == "Pendente":
            total_pendente += 1
            valor_a_receber += mensalidade
        else:
            total_atrasado += 1
            valor_em_atraso += mensalidade

        if busca and id_aluno not in ids_da_busca:
            continue
        if filtro_situacao and situacao != filtro_situacao:
            continue

        situacoes.append((id_aluno, nome_aluno, dia_vencimento, situacao, mes_da_linha))

    total_linhas = len(situacoes)
    situacoes = situacoes[:LIMITE_LINHAS]

    return render_template(
        "financeiro.html",
        situacoes=situacoes,
        total_linhas=total_linhas,
        limite_linhas=LIMITE_LINHAS,
        todos_meses=todos_meses,
        mes=mes,
        busca=busca,
        situacao_filtro=filtro_situacao,
        mes_formatado=f"{mes[5:7]}/{mes[:4]}",
        total_pago=total_pago,
        total_pendente=total_pendente,
        total_atrasado=total_atrasado,
        valor_recebido=valor_recebido,
        valor_a_receber=valor_a_receber,
        valor_em_atraso=valor_em_atraso,
    )


if __name__ == "__main__":
    app.run()