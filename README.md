# iTagRest - Gestão de Restaurante e Emissão Fiscal

Sistema moderno de gestão para restaurantes (bebidas e refeições) com foco em emissão simplificada de NFC-e (Nota Fiscal de Consumidor Eletrônica) utilizando Python e FastAPI.

## 🚀 Stack Tecnológica
- **Linguagem:** Python 3.12+
- **Framework API:** FastAPI
- **Banco de Dados:** PostgreSQL 16
- **ORM:** SQLAlchemy / Alembic
- **Lib Fiscal:** `erpbrasil.nfe` (Padrão Odoo Brasil)

## 🚀 Como Rodar o Sistema (com Docker)

Com o Docker e o Docker Compose instalados, basta um único comando para subir todo o ambiente (Frontend e Backend):

```bash
# Sobe todos os serviços em background e faz o build se necessário
docker-compose up --build -d
```

**URLs de Acesso:**
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend (API Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)

**Banco de Dados:** O sistema irá se conectar ao PostgreSQL rodando no seu computador (`host.docker.internal`). Certifique-se de que ele esteja no ar.

## 🛠 Requisitos
- Docker & Docker Compose
- PostgreSQL rodando localmente (usuário: `root`, senha: `root`)
- Banco de dados `itagrest_db` criado.

## 📂 Estrutura de Documentação
- [Épicos do Projeto](docs/epicos.md)
- [Histórias de Usuário](docs/historias/)
- [Arquitetura e Banco de Dados](docs/arquitetura.md)
