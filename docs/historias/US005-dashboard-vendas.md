# US005: Dashboard de Vendas e Performance

**Épico:** E5 - Retaguarda e Relatórios
**Status:** REFINED (Pronto para Dev)

## 📋 Descrição
Como administrador, quero visualizar um gráfico de desempenho das vendas diárias por produto para entender o que mais sai no meu restaurante e tomar decisões de estoque.

## 🎯 Objetivo de UX (Analítico & Moderno)
- **Visualização de Dados:** Gráfico de barras ou linhas suave (estilo Area Chart) mostrando a quantidade vendida por dia.
- **Interatividade:** Tooltips elegantes ao passar o mouse sobre as barras/pontos do gráfico.
- **Filtro de Período:** Seletor rápido (Hoje, Últimos 7 dias, Este Mês) com animação de transição nos dados.
- **Responsividade:** O gráfico deve se redimensionar (re-render) automaticamente ao girar o celular ou mudar o tamanho da janela.

## ✅ Critérios de Aceitação
1. **Dados do Gráfico:** Agregação de `venda_itens` somando a quantidade por `produto_id` agrupado por dia.
2. **Top Produtos:** Exibição clara dos "Top 5" produtos mais vendidos no período selecionado.
3. **Performance:** A query deve ser otimizada para não travar o dashboard mesmo com milhares de vendas.
4. **Empty State:** Se não houver vendas, exibir um gráfico "fantasma" elegante (skeleton/placeholder) com a mensagem: "Suas vendas aparecerão aqui".

## 🎨 UI/UX Mockup (Next.js + Recharts/Chart.js)
- **Cores:** Paleta moderna (ex: tons de azul e roxo com gradientes suaves).
- **Cards:** Widgets de resumo (Total do Dia, Ticket Médio) acima do gráfico principal.
