# Changelog - iTagRest

Resumo das principais entregas e correções organizadas por versão e data.

## [1.3.0] - 2026-04-22

### Adicionado
- **Estabilidade Docker:** Novo `entrypoint.sh` com loop de espera `pg_isready` para garantir que o banco de dados esteja pronto antes das migrações.
- **Logs Persistentes:** Redirecionamento de logs de inicialização para `storage/logs/backend.log` (montado em volume) para facilitar o diagnóstico de falhas no container.

### Corrigido
- **Emissão Fiscal:** Instalação corrigida da biblioteca `erpbrasil.edoc` e suas dependências de sistema (`libxmlsec1-dev`) no Dockerfile.
- **Porta do Sistema:** Backend alterado da porta 8000 para 8001 para evitar conflitos de porta comuns no host.
- **CORS:** Atualização das origens permitidas para incluir a porta 3001 do frontend.

### Segurança
- **Sinais do Processo:** Ajuste no `entrypoint.sh` para usar `exec` corretamente, permitindo que o Docker gerencie o encerramento do processo Uvicorn de forma limpa.

---

## [1.2.0] - 2026-04-16

### Adicionado
- **Seed Data:** Script `seed_dashboard.py` para geração de massa de dados histórica (365 dias).
- **Dashboard Dinâmico:** Seletor de períodos (7, 15, 30, 365 dias) com agrupamento inteligente (diário/mensal).
- **Feedback Visual (PDV):** Badges de quantidade em tempo real nos itens do cardápio e animação de "Check" ao adicionar produtos.
- **Loading States:** Indicadores de carregamento nos cards de mesas e produtos para evitar cliques múltiplos.

### Corrigido
- **Blindagem de Mesa:** Implementado índice único parcial no PostgreSQL para impedir a abertura de múltiplas comandas ativas para a mesma mesa.
- **Consistência de Dados:** Unificação da lógica de recuperação de vendas entre o Mapa de Mesas e a Comanda Mobile.
- **Layout Cardápio:** Correção do colapso dos cards de produtos em telas pequenas.

### Segurança
- **Integridade de Banco:** Restrição física (Unique Index) para prevenir corrupção lógica de comandas simultâneas.

---

## [1.1.0] - 2026-04-15

### Adicionado
- **Gestão de Clientes:** CRUD completo para identificação nominal em vendas.
- **Impressão Térmica:** Suporte a impressão de 58mm (ESC/POS compatible) para DANFE NFC-e.
- **Comanda Mobile:** Refatoração completa com agrupamento de itens e Drawer de lançamentos.

### Corrigido
- **Estabilidade API:** Correção de crash causado por dependência ausente do ReportLab.
