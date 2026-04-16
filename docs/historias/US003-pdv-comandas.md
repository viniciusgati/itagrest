# US003: PDV Moderno com Gestão de Comandas

**Épico:** E3 - Operação de Venda (PDV)
**Status:** Approved

## 🎯 Story
**As a** operador de caixa ou garçom,
**I want** gerenciar mesas através de comandas eletrônicas e realizar fechamentos com PIX,
**so that** o atendimento seja ágil, visual e integrado ao fluxo fiscal.

## 👥 Executor Assignment
executor: "@dev"
quality_gate: "@architect"
quality_gate_tools: ["pytest", "pylint", "playwright"]

## ✅ Acceptance Criteria
1. **Mapa de Mesas Visual:** Exibir grid de mesas com status (Livre, Em Atendimento, Aguardando Pagamento).
2. **Abertura de Comanda:** Permitir abrir uma mesa (venda) vinculando itens do cardápio (US002).
3. **Lançamento Ágil:** Adição de itens com clique único e animação visual de "voo" para o carrinho lateral.
4. **Cálculo de Total:** Subtotal atualizado em tempo real no painel de checkout.
5. **Checkout PIX Dinâmico:** Gerar QR Code e chave "Copia e Cola" baseados na chave PIX configurada na empresa (US001).
6. **Integração Backend:** Persistir dados nas tabelas `vendas` e `venda_itens` conforme arquitetura.
7. **Fechamento de Mesa:** Após pagamento, liberar a mesa e preparar o status para emissão de NFC-e (US004).

## 🤖 CodeRabbit Integration

### Story Type Analysis
**Primary Type:** API
**Secondary Type(s):** Frontend, Database
**Complexity:** Medium
**Risk Level:** MEDIUM RISK
**Integration Points:** 
- Cardápio (US002) - para busca de produtos.
- Configuração Fiscal (US001) - para chave PIX da empresa.
- Vendas/Itens (Database) - persistência do pedido.

### Specialized Agent Assignment
**Primary Agents:**
- @dev (pre-commit reviews)
- @db-sage (schema validation for vendas/venda_itens)

**Supporting Agents:**
- @ux-expert (visual feedback and mobile-first layout)

### Quality Gate Tasks
- [ ] Pre-Commit (@dev): Validação de tipos e linting.
- [ ] Pre-PR (@architect): Revisão de lógica de fechamento de venda e integridade do PIX.

### CodeRabbit Focus Areas
**Primary Focus:**
- Regressão: Garantir que o cardápio (US002) continua funcionando.
- Segurança: Validar que apenas mesas ativas podem receber itens.
- Performance: Cálculos de total eficientes no frontend e backend.

**Secondary Focus:**
- UX: Animações fluidas e feedback visual claro de erro.
- Error Handling: Tratar falha na geração do payload PIX.

## 🛠️ Tasks / Subtasks

- [x] **Task 1: Backend - Modelagem e Persistência**
  - [x] Criar `app/models/venda.py` com classes `Venda` e `VendaItem`.
  - [x] Criar schemas Pydantic em `app/schemas/venda.py`.
  - [x] Criar endpoints `POST /api/v1/vendas` (abrir/atualizar) e `GET /api/v1/vendas/mesas` (status).
  - [x] Implementar lógica de geração de Payload PIX.

- [x] **Task 2: Frontend - Interface do PDV**
  - [x] Criar `/frontend/src/app/pdv` com Grid de Mesas responsivo.
  - [x] Implementar Painel Lateral (Carrinho) com integração ao cardápio da US002.
  - [x] Adicionar animação de entrada com `framer-motion`.

- [x] **Task 3: Checkout e PIX**
  - [x] Criar Modal de Checkout com exibição de QR Code PIX (`qrcode.react`).
  - [x] Implementar botão de fechamento que limpa a mesa e redireciona.

- [x] **Task 4: Testes e Validação**
  - [x] Testes unitários para cálculo de total e geração de payload PIX.
  - [x] Teste E2E (Playwright) do fluxo completo: Abrir mesa -> Adicionar item -> Gerar PIX.

## 📝 Dev Agent Record (Dex)

### Status: DONE
### Agent Model Used: Gemini 2.0 Flash

### 📝 Change Log
- 2026-04-15: Implementação completa do Backend de Vendas (Models, Schemas, Endpoints).
- 2026-04-15: Implementação da interface do PDV no Frontend com Framer Motion e QRCode.react.
- 2026-04-15: Integração do fluxo de checkout PIX com geração de payload dinâmico.
- 2026-04-15: Ajuste para permitir cancelamento/estorno de comandas e timeout de 1 minuto no PIX com cronômetro visual.

### 📂 File List
- `app/models/venda.py`
- `app/schemas/venda.py`
- `app/api/v1/endpoints/vendas.py`
- `app/main.py`
- `frontend/src/app/pdv/page.tsx`

## 🛡️ QA Results (Quinn)
*(To be populated by @qa)*
