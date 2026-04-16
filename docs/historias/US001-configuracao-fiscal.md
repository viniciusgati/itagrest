# US001: Wizard de Ativação Fiscal (Certificado A1)

**Épico:** E1 - Configuração Fiscal
**Status:** COMPLETED

## 📋 Descrição
Como administrador, quero ser guiado por um assistente de configuração (Wizard) para realizar o upload do certificado digital (apenas formato .pfx) e configurar meus dados fiscais, garantindo que o sistema esteja apto a emitir NFC-e.

## 🎯 Objetivo de UX (Moderno & Animado)
- **Trigger de Entrada:** Ao logar pela primeira vez, o Dashboard exibe uma animação de "Luz de Foco" ou um Modal com fundo desfocado (blur) convidando para a ativação.
- **Passo a Passo (Wizard):**
  1. **Dados da Empresa:** CNPJ, Razão Social e Inscrição Estadual (Busca automática via API se possível).
  2. **Certificado Digital:** Drag & Drop para o arquivo estritamente .pfx e campo de senha com "olho" para visualizar.
  3. **Ambiente & CSC:** Escolha entre Homologação/Produção e inserção dos tokens da SEFAZ.
- **Visual:** Barra de progresso circular ou linear com micro-interações (confete ou checkmark animado ao concluir).

## ✅ Critérios de Aceitação
1. **Animação de Boas-Vindas:** O sistema só exibe o convite se `empresa.configurado` for falso.
2. **Upload Seguro:** O certificado deve ser armazenado em diretório protegido (`storage/certs/`).
3. **Validação do PFX:** A API deve tentar abrir o certificado com a senha fornecida para validar antes de salvar.
4. **Responsividade:** O Wizard deve ser fácil de preencher no celular (inputs grandes e botões claros).

## 🛠️ Tarefas
- [x] T1: Backend - Schemas Pydantic para Empresa e Certificado
- [x] T2: Backend - Endpoint POST /api/v1/empresa/configurar
- [x] T3: Backend - Validação e Upload seguro do Certificado (.pfx)
- [x] T4: Frontend - Página e Wizard (Multi-step) de Ativação Fiscal
- [x] T5: Integração Frontend/Backend e Finalização

## 📝 Dev Agent Record (Dex)

### Status: Ready for Review
### Agent Model Used: Gemini 2.0 Flash

### 📝 Change Log
- 2026-04-15: Inicialização das tarefas técnicas para a US001.
- 2026-04-15: Backend completo (Schemas, Endpoints de configuração e upload de certificado com validação PFX).
- 2026-04-15: Frontend completo (Wizard multi-step em `/wizard-fiscal`) e integração finalizada.

### 🐛 Debug Log
- N/A

### ✅ Completion Notes
- O sistema agora permite configurar a empresa e validar o certificado PFX.
- O certificado é salvo em `storage/certs/` e os dados na tabela `empresas`.

## 🛡️ QA Results (Quinn)

### Gate Decision: 🟢 PASS
**Data:** 2026-04-15

#### Observações Técnicas:
1. **Validação:** Verificada implementação de `cryptography` para validação de integridade e senha do PFX antes do upload. Funciona conforme esperado.
2. **Segurança:** Upload direcionado para `storage/certs/`. Identificado que a senha do certificado é armazenada em texto plano; registrado como **Débito Técnico (Segurança)** para futura implementação de criptografia simétrica no campo `certificado_senha`.
3. **UX/UI:** Wizard multi-step implementado com estados de erro claros e transições fluidas. Aderente ao mockup conceitual.

#### Traceability Matrix:
- [x] AC1: Animação de Boas-Vindas baseada em `empresa.configurado`.
- [x] AC2: Upload seguro em `storage/certs/`.
- [x] AC3: Validação funcional do PFX via API.
- [x] AC4: Design responsivo verificado no código do componente.

### 📂 File List
- `docs/historias/US001-configuracao-fiscal.md` (Modified)
- `app/schemas/empresa.py` (Created)
- `app/api/v1/endpoints/empresa.py` (Created)
- `app/services/certificado.py` (Created)
- `app/main.py` (Modified)
- `frontend/src/app/wizard-fiscal/page.tsx` (Created)
