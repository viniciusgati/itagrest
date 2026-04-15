# US000: Setup Inicial do Administrador

**Épico:** E0 - Setup Inicial (Admin Bootstrap)
**Status:** DRAFT (Refinando)

## 📋 Descrição
Como primeiro usuário do sistema, quero definir meu login e senha de administrador para que eu possa acessar o sistema com segurança e começar as configurações fiscais.

## 🎯 Objetivo de UX (Moderno & Simplificado)
- **Zero Atrito:** Se o sistema detectar que não existem usuários, ele redireciona automaticamente para esta tela de "Bem-vindo".
- **Visual:** Layout limpo, centralizado, com foco total no formulário. Uso de cores sóbrias e fontes modernas (ex: Inter).
- **Feedback:** Erros de validação (ex: senhas que não coincidem) devem aparecer instantaneamente, sem precisar clicar no botão.

n> ⚠️ **Nota Técnica:** O envio de e-mail real está **FORA DE ESCOPO** nesta fase. Apenas valide o formato e grave no banco.

## ✅ Critérios de Aceitação
1. **Detecção de Estado:** O sistema deve verificar se a tabela `usuarios` está vazia. Se estiver, a API deve expor um endpoint temporário de bootstrap.
2. **Criação de Conta:**
   - Campo: Nome Completo (Ex: João Silva)
   - Campo: E-mail (Ex: admin@restaurante.com.br)
   - Campo: Usuário (Ex: admin)
   - Campo: Senha (Mínimo 8 caracteres, validada visualmente)
3. **Segurança:** A senha deve ser criptografada (Hashed) no banco usando BCrypt ou similar.
4. **Responsividade:** O formulário deve se ajustar perfeitamente em dispositivos móveis e desktop (Mobile-First).
5. **Transição:** Após a criação, o usuário deve ser logado automaticamente e redirecionado para o **Dashboard Principal**.

## 🎨 UI/UX Mockup (Conceitual)
- **Container:** Card branco com sombras suaves em fundo cinza claríssimo.
- **Input:** Bordas arredondadas (Rounded-lg), foco com contorno azul suave.
- **Botão:** Gradiente moderno (ex: Indigo para Violeta) com efeito de "hover".
