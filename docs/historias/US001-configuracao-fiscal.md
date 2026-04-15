# US001: Wizard de Ativação Fiscal (Certificado A1)

**Épico:** E1 - Configuração Fiscal
**Status:** REFINED (Pronto para Dev)

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

## 🎨 UI/UX Mockup (Next.js + Tailwind)
- **Fundo:** Overlay sutil (backdrop-blur-sm).
- **Wizard:** Centralizado, branco puro, cantos arredondados (rounded-2xl).
- **Progresso:** Steps com cores vibrantes (Success Green para concluído).
