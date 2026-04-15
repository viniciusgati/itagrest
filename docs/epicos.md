# Épicos do Projeto (Roadmap)

Os épicos estão organizados por **prioridade técnica e de negócio**.

## ⚪ E0: Setup Inicial (Admin Bootstrap)
**Prioridade:** CRÍTICA (Bloqueador)
Primeira tela do sistema quando o banco está vazio. Solicita criação do usuário admin.

## 🔴 E1: Configuração Fiscal (Wizard de Ativação)
**Prioridade:** CRÍTICA (Bloqueador)
O sistema deve permitir que o dono do restaurante configure seus dados fiscais (CNPJ, IE) e faça o upload do certificado digital A1 (.pfx). Sem isso, não existe software fiscal.

## 🟠 E2: Gestão do Cardápio (Produtos e Tributos)
**Prioridade:** ALTA
Cadastro de bebidas e refeições. Cada item deve ter obrigatoriamente um código NCM (Nomenclatura Comum do Mercosul) e um CFOP (Código Fiscal de Operações e Prestações) para que o cálculo de imposto seja automático na hora da venda.

## 🟡 E3: Operação de Venda (PDV - Ponto de Venda)
**Prioridade:** ALTA
Abertura de mesas, adição de itens à comanda (bebidas e refeições) e fechamento da conta com escolha de forma de pagamento (Dinheiro, Cartão, PIX).

## 🟢 E4: Emissão e Transmissão de NFC-e
**Prioridade:** MÉDIA (Depende de E1, E2 e E3)
Transformar a venda finalizada em um XML assinado digitalmente, enviar para a SEFAZ via `erpbrasil.nfe` e gerar o PDF da DANFE com QR Code para impressão térmica.

## 🔵 E5: Retaguarda e Relatórios
**Prioridade:** BAIXA
Histórico de vendas, cancelamento de notas dentro do prazo legal e exportação do XML para o contador (fechamento de mês).
