# Academia Flask

Sistema web de gerenciamento de academia, feito com Python e Flask, usando banco de dados PostgreSQL.

Esta é a **versão 2** do projeto (PostgreSQL). A **versão 1**, com SQLite, está na branch `main` (tag `v1.0`).

**Site no ar:** https://academia-flask.onrender.com

O site usa o plano gratuito do Render: depois de um tempo sem acessos ele "adormece", e o primeiro acesso leva cerca de 1 minuto para carregar. O banco de dados gratuito também tem prazo de validade, então o site pode sair do ar. Veja os prints abaixo.

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
- PostgreSQL (com a biblioteca psycopg)
- Docker (PostgreSQL no computador local)
- Gunicorn e Render (publicação)
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

4. Suba um servidor PostgreSQL com Docker (troque `SUA_SENHA` por uma senha de letras e números):

```
docker run --name academia_postgres -e POSTGRES_USER=academia_flask -e POSTGRES_PASSWORD=SUA_SENHA -e POSTGRES_DB=academia_flask -p 5436:5432 -v academia_pgdata:/var/lib/postgresql/data -d postgres:16
```

5. Crie um arquivo chamado `.env` na pasta do projeto, com estas linhas (troque os valores):

```
SECRET_KEY=troque-por-um-texto-longo-e-secreto
DATABASE_URL=postgresql://academia_flask:SUA_SENHA@localhost:5436/academia_flask
ADMIN_SENHA=senha-do-administrador
```

6. Crie as tabelas e o usuário administrador:

```
python criar_banco.py
```

7. Rode o sistema:

```
python app.py
```

8. Abra no navegador: http://127.0.0.1:5000

## Primeiro acesso

O `criar_banco.py` cria um usuário administrador:

- Login: `admin@academia.com`
- Senha: a que você definiu em `ADMIN_SENHA`

A senha não fica escrita no código: ela vem do arquivo `.env` (no computador) ou das variáveis de ambiente (no Render).

## Publicação no Render

- Banco: PostgreSQL do Render (plano gratuito)
- Site: Web Service ligado a esta branch (`postgresql`)
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Variáveis de ambiente: `DATABASE_URL`, `SECRET_KEY` e `ADMIN_SENHA`

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
