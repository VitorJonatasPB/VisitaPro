# Projeto Rota99

Este projeto é um sistema construído com **Django** e **Django REST Framework**, gerenciado através do **Poetry**.

## Pré-requisitos

Para rodar este projeto na sua máquina, você vai precisar ter instalado:

- [Python](https://www.python.org/downloads/) (versão >= 3.14)
- [Poetry](https://python-poetry.org/docs/#installation) (para instalar e gerenciar as bibliotecas)
- **Git** (para clonar o repositório)

## Como Rodar o Projeto (Manual)

Se você estiver em um sistema que não usa os scripts `.bat` ou preferir fazer tudo pelo terminal, siga o passo a passo padrão:

**1. Clone o repositório:**
```bash
git clone https://github.com/SEU-USUARIO/rota99.git
cd rota99
```

**2. Instale as dependências com o Poetry:**
Como o projeto usa o arquivo `pyproject.toml`, o Poetry vai gerenciar todas as versões pra você.
```bash
poetry install
```

**3. Ative o ambiente virtual (se necessário):**
```bash
poetry shell
```

**4. Rode as migrações do Banco de Dados:**
```bash
python manage.py migrate
```

**5. Inicie o Servidor:**
```bash
python manage.py runserver
```

Após isso, o sistema deve ficar acessível normalmente pelo seu navegador ou ferramentas como o Postman na porta padrão do Django (`http://127.0.0.1:8000`).

---

**Nota:** Por motivos de segurança, arquivos sensíveis (como `.env` e o banco de dados `db.sqlite3`) estão em nosso `.gitignore` e não devem ir para o GitHub. Certifique-se de configurar suas chaves locais para que o sistema funcione.
