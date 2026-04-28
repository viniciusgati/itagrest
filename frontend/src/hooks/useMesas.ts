'use client';

import { useState, useEffect, useCallback } from 'react';
import { vendaService } from '@/services/venda.service';

export interface Mesa {
  mesa: number;
  venda_id?: number;
  status: 'LIVRE' | 'EM_ATENDIMENTO' | 'AGUARDANDO_PAGAMENTO' | 'PAGA' | 'CANCELADA';
  total: number;
}

export function useMesas() {
  const [mesas, setMesas] = useState<Mesa[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMesas = useCallback(async () => {
    try {
      setLoading(true);
      const data = await vendaService.getMesas();
      setMesas(data);
      setError(null);
    } catch (err) {
      console.error('Erro ao buscar mesas:', err);
      setError('Não foi possível carregar o mapa de mesas.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Busca inicial
  useEffect(() => {
    fetchMesas();
  }, [fetchMesas]);

  return { mesas, loading, error, refresh: fetchMesas };
}
