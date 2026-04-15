# US004: Emissão e Transmissão de NFC-e

**Épico:** E4 - Emissão e Transmissão de NFC-e
**Status:** DRAFT (Refinando)

## 📋 Descrição
Como administrador, quero que cada venda finalizada seja transmitida para a SEFAZ automaticamente, garantindo a legalidade da operação.

## ✅ Critérios de Aceitação
1. **Transmissão em Background:** Após o checkout (US003), o sistema tenta transmitir a nota sem travar a tela do operador.
2. **Tratamento de Erros:** Se a SEFAZ rejeitar (NCM inválido, etc), a nota deve aparecer no Dashboard (US005) como "Rejeitada" com o motivo claro.
3. **Impressão Térmica:** Gerar o PDF da DANFE simplificada formatado para bobinas de 80mm/58mm.
4. **Histórico:** Permitir retransmitir notas que falharam após correção dos dados.
