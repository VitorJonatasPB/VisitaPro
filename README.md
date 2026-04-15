# Projeto Rota99

**Rota99:** é um sistema que foi criado para organizar e controlar as visitas que os consultores fazem nas escolas. Ele tem duas partes principais: um painel na web onde fica todo o cadastro (das escolas, professores, regiões, etc.) e um aplicativo de celular que o consultor usa na rua para registrar que chegou na escola e preencher os relatórios.

---

## Arquitetura do Sistema

O sistema foi dividido em três camadas principais:

- **Back-end (Django + DRF):** Responsável pela regra de negócio, autenticação e persistência dos dados.
- **Front-end Web (Django Templates):** Utilizado para o painel administrativo e cadastro, foi escolhido pela simplicidade e rapidez no desenvolvimento.
- **Mobile (React Native):** Responsável pela coleta de dados em campo, com suporte offline e sincronização com a API.

---

## Stack

### Back-end (A nossa API e o Painel Web)

- **Python e Django:** O back-end foi desenvolvido em Python utilizando o Django (versão 6), escolhido por sua facilidade de uso e criação de APIs.
- **Django REST Framework (DRF):** Utilizado para criar os endpoints da API que o aplicativo do celular consome. O **SimpleJWT** é usado para autenticação e gerenciamento de tokens de acesso.
- **Banco de Dados:** O sistema utiliza **SQLite** em ambiente de desenvolvimento, pela simplicidade e facilidade de uso, e está configurado para **PostgreSQL** em produção, com o uso da biblioteca _psycopg_.
- **Painel Administrativo:** O painel de administração do Django foi customizado com o _django-jazzmin_, proporcionando uma interface mais moderna e amigável.
- **Gerenciamento de Dependências:** O **Poetry** é utilizado para gerenciar as dependências do projeto, garantindo o controle de versões e a reprodutibilidade do ambiente.

### Front-end (O site principal / Páginas da Web)

- **Django Templates (HTML/CSS):** A interface das telas que abrem no navegador do computador é desenvolvida utilizando o sistema de _Templates_ nativo do Django. Os arquivos HTML são criados dentro da pasta `frontend/templates` e o Django é responsável por renderizar as páginas com as informações do banco de dados. A escolha por essa abordagem foi visando agilidade na entrega e simplicidade na manutenção, evitando a complexidade de integrações com bibliotecas JavaScript pesadas como React.js.

### App Mobile (Aplicativo do Consultor)

- **React Native com Expo:** O aplicativo que o consultor instala no celular foi feito com React Native, usando o Expo (versão 54). Com o mesmo código, é possível gerar o app tanto para Android quanto para iPhone.
- **TypeScript:** O código foi escrito em TypeScript, o que permite a detecção de erros em tempo de desenvolvimento, evitando bugs comuns em JavaScript puro.
- **Requisições para a API:** O `@tanstack/react-query` é utilizado para realizar as requisições à API do Django, gerenciando o carregamento de dados, cache e proporcionando uma experiência fluida ao usuário.

---

## Funcionalidades do Aplicativo

- **Ponto com GPS (Check-in e Check-out):** O aplicativo utiliza o _expo-location_ para capturar a localização do consultor no momento do check-in e check-out, enviando as coordenadas para o back-end para validação de proximidade com a escola.
- **Responder Questionários:** O sistema permite a criação de questionários dinâmicos pelo painel web, que são exibidos ao consultor no aplicativo para coleta de informações, notas e status de arquivos.
- **Assinatura na Tela:** A funcionalidade de assinatura é implementada através do _react-native-signature-canvas_, permitindo que o consultor colete a assinatura do responsável na tela do dispositivo. A assinatura é convertida em string (Base64) e salva no servidor.
- **Modo Offline:** O aplicativo suporta operação offline, armazenando as respostas localmente utilizando o _AsyncStorage_ e sincronizando com o back-end quando a conexão com a internet é restabelecida.
- **Reportar o Bug:** Uma funcionalidade de reporte de bugs permite que o consultor envie informações detalhadas sobre erros ocorridos no aplicativo, facilitando o diagnóstico e correção de problemas.

---

## Pré-requisitos

Para rodar este projeto na sua máquina, você vai precisar ter instalado:

- [Python](https://www.python.org/downloads/) (versão >= 3.14)
- [Poetry](https://python-poetry.org/docs/#installation) (para instalar e gerenciar as bibliotecas)
- **Git** (para clonar o repositório)

## Como Rodar o Projeto (Manual)

Siga o passo a passo padrão:

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
