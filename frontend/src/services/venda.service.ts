import api from '@/lib/api';

export interface VendaItemCreate {
  produto_id: number;
  quantidade: number;
  preco_customizado?: number;
}

export interface FaturarVendaPayload {
  status: 'PAGA' | 'CANCELADA';
  forma_pagamento: 'DINHEIRO';
  cliente_id?: number;
}

export const vendaService = {
  /**
   * Busca o mapa de mesas atualizado
   */
  async getMesas() {
    const res = await api.get('/vendas/mesas');
    return res.data;
  },

  /**
   * Abre uma nova mesa ou recupera a ativa
   */
  async abrirVenda(mesa: number) {
    const res = await api.post('/vendas/', { mesa });
    return res.data;
  },

  /**
   * Adiciona um item à venda (suporta preço customizado)
   */
  async adicionarItem(vendaId: number, item: VendaItemCreate) {
    const res = await api.post(`/vendas/${vendaId}/itens`, item);
    return res.data;
  },

  /**
   * Remove um item da venda
   */
  async removerItem(vendaId: number, itemId: number) {
    const res = await api.delete(`/vendas/${vendaId}/itens/${itemId}`);
    return res.data;
  },

  /**
   * Finaliza a venda (faturamento)
   */
  async faturarVenda(vendaId: number, payload: FaturarVendaPayload) {
    const res = await api.put(`/vendas/${vendaId}/fechar`, payload);
    return res.data;
  },

  /**
   * Cancela uma venda aberta
   */
  async cancelarVenda(vendaId: number) {
    const res = await api.delete(`/vendas/${vendaId}/cancelar`);
    return res.data;
  },

  /**
   * Cancela uma NFC-e autorizada junto a SEFAZ
   */
  async cancelarNota(vendaId: number, justificativa: string) {
    const res = await api.post(`/notas/cancelar/${vendaId}`, { justificativa });
    return res.data;
  }
};
