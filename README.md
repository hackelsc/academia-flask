# Academia Flask

Sistema web de gerenciamento de academia, feito com Python e Flask, usando banco de dados SQLite.

Esta é a **versão 1** do projeto. A versão 2, com PostgreSQL, será desenvolvida em outra branch.

## O que o sistema faz

- Login com controle de acesso por perfil
- Cadastro e consulta de alunos
- Cadastro e consulta de funcionários
- Turmas
- Financeiro (mensalidades e pagamentos, com filtros)
- Páginas institucionais

## Tecnologias

- Python 3
- Flask
- SQLite
- HTML e CSS

## Como rodar no seu computador

1. Baixe o projeto e abra a pasta dele no terminal.

2. Crie e ative o ambiente virtual:

```
python -m venv .venv
.venv\Scripts\activate
```

3. Instale as bibliotecas:

```
pip install -r requirements.txt
```

4. Crie um arquivo chamado `.env` na pasta do projeto, com esta linha (troque o valor por um texto longo e secreto qualquer):

```
SECRET_KEY=troque-por-um-texto-secreto
```

5. Crie o banco de dados:

```
python criar_banco.py
```

6. Rode o sistema:

```
python app.py
```

7. Abra no navegador: http://127.0.0.1:5000

## Primeiro acesso

O banco já vem com um usuário administrador:

- Login: `admin@academia.com`
- Senha: `trocar123`

**Troque essa senha assim que entrar pela primeira vez.**

## Estrutura do projeto

- `app.py`: rotas e regras do sistema
- `funcoes_banco.py`: funções que acessam o banco
- `criar_banco.py`: cria as tabelas do banco
- `templates/`: páginas HTML
- `static/`: arquivos de estilo (CSS)

## Telas do sistema

### Login
![Login](prints/01-login.png)

### Painel
![Painel](prints/02-painel.png)

### Alunos
![Alunos](prints/03-alunos.png)

### Financeiro
![Financeiro](prints/04-financeiro.png)

### Turmas
![Turmas](prints/05-turmas.png)
