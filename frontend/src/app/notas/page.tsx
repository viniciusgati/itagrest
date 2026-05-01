'use client'

import { useState, useEffect } from 'react'
import { FileText, CheckCircle2, AlertCircle, Search, Printer, XCircle, ExternalLink } from 'lucide-react'
import api, { getImageUrl } from '@/lib/api'
import Link from 'next/link'

export default function MonitorFiscalPage() {
  const [notas, setNotas] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchNotas = async () => {
    setLoading(true)
    try {
      const res = await api.get('/notas/todas')
      setNotas(res.data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    fetchNotas()
  }, [])

  const getStatusBadge = (nota: any) => {
    if (nota.protocolo_cancelamento) {
      return {
        bg: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
        icon: XCircle,
        label: 'Cancelada',
      }
    }
    if (nota.status_sefaz === '100') {
      return {
        bg: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400',
        icon: CheckCircle2,
        label: 'Autorizada',
      }
    }
    return {
      bg: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
      icon: AlertCircle,
      label: 'Erro',
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-6 md:p-10 font-sans transition-colors duration-300">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
          <div>
            <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight">Monitor Fiscal</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1 font-medium">Gestão de NFC-e (Modelo 65) emitidas.</p>
          </div>
          <button 
            onClick={fetchNotas}
            className="bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-900 dark:text-white font-bold px-6 py-3 rounded-2xl transition-all border border-slate-200 dark:border-slate-700 shadow-sm flex items-center gap-2"
          >
            <FileText className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Atualizar
          </button>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-[2.5rem] shadow-xl shadow-slate-200/50 dark:shadow-none border border-slate-100 dark:border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/50 dark:bg-slate-900/50 border-b border-slate-100 dark:border-slate-700">
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">ID / Venda</th>
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Chave de Acesso</th>
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Protocolo</th>
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Status SEFAZ</th>
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 dark:divide-slate-700">
                {notas.map((nota: any) => {
                  const badge = getStatusBadge(nota)
                  return (
                    <tr key={nota.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-700/20 transition-colors group">
                      <td className="p-6 font-bold text-slate-900 dark:text-white">#{nota.id} <span className="text-slate-400 dark:text-slate-500 font-medium block text-xs">Venda #{nota.venda_id}</span></td>
                      <td className="p-6 font-mono text-xs text-slate-500 dark:text-slate-400">{nota.chave_acesso || 'Pendente'}</td>
                      <td className="p-6 text-sm text-slate-600 dark:text-slate-400 font-medium">
                        {nota.protocolo_cancelamento || nota.protocolo || '-'}
                        {nota.protocolo_cancelamento && <span className="block text-[10px] text-red-500 font-bold uppercase">Cancelamento</span>}
                      </td>
                      <td className="p-6">
                        <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest ${badge.bg}`}>
                          <badge.icon className="w-3 h-3" />
                          {badge.label}
                        </div>
                      </td>
                      <td className="p-6 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Link
                            href={`/notas/${nota.venda_id}`}
                            className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white transition-all shadow-lg"
                            title="Detalhes"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </Link>
                          {nota.status_sefaz === '100' && !nota.protocolo_cancelamento && (
                            <button 
                              onClick={() => {
                                const token = localStorage.getItem('token');
                                window.open(getImageUrl(`/api/v1/notas/${nota.venda_id}/imprimir?token=${token}`), '_blank');
                              }}
                              className="p-2 bg-slate-900 dark:bg-brand-600 hover:bg-slate-800 dark:hover:bg-brand-700 rounded-lg text-white transition-all shadow-lg" 
                              title="Imprimir DANFE"
                            >
                              <Printer className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
                {notas.length === 0 && !loading && (
                  <tr>
                    <td colSpan={5} className="p-20 text-center text-slate-400 dark:text-slate-500 font-medium">
                      Nenhuma nota emitida ainda.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}