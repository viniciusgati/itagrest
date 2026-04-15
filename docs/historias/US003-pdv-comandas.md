# US003: PDV Moderno com Gestão de Comandas

**Épico:** E3 - Operação de Venda (PDV)
**Status:** REFINED (Pronto para Dev)

## 📋 Descrição
Como operador de caixa/garçom, quero gerenciar as mesas do restaurante através de comandas eletrônicas, adicionando itens com facilidade e realizando o fechamento com PIX dinâmico.

## 🎯 Objetivo de UX (Ágil & Visual)
- **Mapa de Mesas:** Interface visual com "Cards de Mesas".
  - **Verde:** Livre.
  - **Amarelo:** Em atendimento (com tempo de permanência).
  - **Vermelho:** Aguardando fechamento/pagamento.
- **Lançamento Rápido:** Ao clicar na mesa, abre-se o cardápio (US002). Um clique no item já o adiciona à comanda com animação de "voo" para o carrinho.
- **Checkout PIX:** Botão destacado "Pagar com PIX". Ao clicar, gera um **QR Code centralizado** na tela com o valor total da venda.

## ✅ Critérios de Aceitação
1. **Controle de Comanda:** Cada venda aberta deve estar vinculada a um `numero_mesa`.
2. **Adição de Itens:** Deve permitir adicionar múltiplos itens, alterar quantidade e remover (com confirmação).
3. **Geração de PIX:** O sistema deve gerar a linha do "PIX Copia e Cola" e o QR Code baseado na chave configurada na empresa.
4. **Fechamento Automático:** Ao confirmar o pagamento, o status da mesa volta para "Livre" (Verde) e a venda é enviada para o fluxo fiscal (E4).
5. **Responsividade:** Layout otimizado para tablets (uso lateral) e PC (uso com mouse).

## 🎨 UI/UX Mockup (Next.js + Tailwind)
- **Grid de Mesas:** Flexbox/Grid responsivo com cards `hover:scale-105`.
- **Painel Lateral:** Carrinho de compras flutuante com subtotal em tempo real.
- **Modal de PIX:** Minimalista, com botão "Copiar Código" e cronômetro de expiração (opcional).
