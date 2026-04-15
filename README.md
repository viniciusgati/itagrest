# iTagRest - Gestão de Restaurante e Emissão Fiscal

Sistema moderno de gestão para restaurantes (bebidas e refeições) com foco em emissão simplificada de NFC-e (Nota Fiscal de Consumidor Eletrônica) utilizando Python e FastAPI.

## 🚀 Stack Tecnológica
- **Linguagem:** Python 3.12+
- **Framework API:** FastAPI
- **Banco de Dados:** PostgreSQL 16
- **ORM:** SQLAlchemy / Alembic
- **Lib Fiscal:** `erpbrasil.nfe` (Padrão Odoo Brasil)

## 🛠 Configuração de Desenvolvimento
1. **Banco de Dados (Postgres):**
   - Host: `localhost`
   - Porta: `5432`
   - Usuário/Senha: `root` / `root`
   - Database: `itagrest_db`

2. **Variáveis de Ambiente:**
   Copie o arquivo `.env.example` para `.env` e ajuste as credenciais.

3. **Instalação:**
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

## 📂 Estrutura de Documentação
- [Épicos do Projeto](docs/epicos.md)
- [Histórias de Usuário](docs/historias/)
- [Arquitetura e Banco de Dados](docs/arquitetura.md)
