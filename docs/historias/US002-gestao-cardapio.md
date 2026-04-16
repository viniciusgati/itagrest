# US002: Gestão do Cardápio Moderno

**Épico:** E2 - Gestão do Cardápio
**Status:** READY

## 📋 Descrição
Como administrador, quero cadastrar meus produtos com fotos, preços e dados fiscais completos para que o PDV seja visualmente atraente e esteja em conformidade com a legislação tributária.

## 🎯 Objetivo de UX (Visual & Rápido)
- **Grid de Imagens:** Visualização dos produtos em cards com fotos grandes e arredondadas (Rounded-2xl).
- **Upload Inteligente:** Redimensionamento automático no frontend (Canvas API) para no máximo 800x800px antes do upload.
- **Filtros Rápidos:** Navegação por abas ou chips de categoria (Bebidas, Refeições, Outros) com contagem de itens.
- **Feedback Visual:** Skeleton loading enquanto as imagens carregam para evitar "layout shift".

## ✅ Critérios de Aceitação

### 1. Cadastro e Listagem
- **Campos Obrigatórios:** Descrição (mínimo 3 caracteres), Preço de Venda (positivo), Unidade (UN, KG, LT), Categoria (BEBIDA, REFEICAO, OUTROS).
- **Campos Fiscais:** NCM (obrigatório, 8 dígitos), CFOP (obrigatório, 4 dígitos), CEST (opcional, 7 dígitos).
- **Listagem:** Grid responsivo (1 col mobile, 3-4 cols desktop).

### 2. Gerenciamento de Imagens
- **Formatos Aceitos:** JPG, PNG, WebP (max 5MB).
- **Placeholder:** Se não houver foto, exibir um círculo com o gradiente da marca e as duas primeiras letras da descrição.
- **Remoção:** Opção de excluir a foto e voltar ao placeholder sem excluir o produto.

### 3. Persistência e Segurança
- **API:** Implementar CRUD completo em `/api/v1/produtos`.
- **Validação de Erro:** Retornar mensagens claras caso NCM/CFOP sejam inválidos.
- **Acesso:** Endpoint protegido - apenas usuários autenticados podem realizar alterações.

## 🎨 UI/UX Mockup (Conceitual)
- **Card:** Fundo branco, sombra suave (shadow-md), imagem no topo ocupando 60% do card.
- **Preço:** Destaque em negrito e cor contrastante (ex: Emerald-600).
- **Botão Adicionar:** No topo da página, fixo em telas menores (FAB).

## 🛠️ Tarefas
- [x] T1: Backend - Modelo SQLAlchemy `Produto` em `app/models/produto.py`
- [x] T2: Backend - Schemas Pydantic para Produto (Create, Update, Response)
- [x] T3: Backend - Endpoints CRUD para Produtos em `app/api/v1/endpoints/produtos.py`
- [x] T4: Backend - Serviço de Upload de imagens e placeholders (`app/services/imagem.py`)
- [x] T5: Frontend - Página de Cardápio (`frontend/src/app/cardapio`) com Grid de Cards
- [x] T6: Frontend - Componente de Card e Filtros (Bebidas, Refeições, Outros)
- [x] T7: Frontend - Modal de Formulário com Preview de Imagem (Canvas API)
- [x] T8: Integração e Validação Final (CRUD completo + Upload)

## 📝 Dev Agent Record (Dex)

### Status: Completed
### Agent Model Used: Gemini 2.0 Flash

### 📝 Change Log
- 2026-04-15: Inicialização da implementação da US002 e planejamento das tarefas.
- 2026-04-15: Finalização do CRUD de produtos, upload de imagens com Canvas API e interface de gestão de cardápio.

### 📂 File List
- `app/models/produto.py`
- `app/schemas/produto.py`
- `app/api/v1/endpoints/produtos.py`
- `app/services/imagem.py`
- `app/main.py`
- `frontend/src/app/cardapio/page.tsx`

## QA Results
### Review Date: N/A
### Reviewed By: N/A
### Gate Status: PENDING

## Change Log
- 2026-04-15: Pax (PO) - Refinamento completo: Adição de campos fiscais (CEST/Unidade), especificações de UX (Canvas API/Skeleton) e validações de API.
