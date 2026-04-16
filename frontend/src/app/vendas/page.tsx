'use client'

import { useState, useEffect } from 'react'
import { ArrowLeft, Search, FileText, Code, CheckCircle2, XCircle, Clock, ExternalLink, Loader2 } from 'lucide-react'
import axios from 'axios'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'

const API_VENDAS = 'http://localhost:8000/api/v1/vendas'

export default function VendasMonitorPage() {
  const [vendas, setVendas] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearch] = useState('')
  const [logView, setLogView] = useState<string | null>(null)

  const fetchVendas = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API_VENDAS}/lista`)
      setVendas(res.data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    fetchVendas()
  }, [])

  const handleViewXml = (vendaId: int) => {
    window.open(`${API_VENDAS}/${vendaId}/log-xml`, '_blank')
  }

  const handleViewLog = async (vendaId: int) => {
    try {
      const res = await axios.get(`${API_VENDAS}/${vendaId}/log-texto`)
      setLogView(res.data.log)
    } catch (err) { alert("Log não disponível.") }
  }

  const filteredVendas = vendas.filter(v => 
    v.id.toString().includes(searchTerm) || 
    v.mesa.toString().includes(searchTerm)
  )

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-6 md:p-10 font-sans transition-colors duration-300">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header de Navegação */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl flex items-center justify-center shadow-sm border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
              <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-300" />
            </Link>
            <div>
              <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Monitor de Operações</h1>
              <p className="text-slate-400 dark:text-slate-500 font-medium">Histórico de vendas e auditoria SEFAZ</p>
            </div>
          </div>
        </div>

        {/* Barra de Filtros */}
        <div className="bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-xl shadow-slate-200/40 dark:shadow-none flex flex-col md:flex-row gap-4 items-center text-slate-900 dark:text-white">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input 
              type="text" 
              placeholder="Buscar por Mesa ou ID da Venda..."
              className="w-full pl-14 pr-6 py-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border-none focus:ring-4 focus:ring-brand-100 dark:focus:ring-brand-900/20 outline-none font-medium transition-all"
              value={searchTerm}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button onClick={fetchVendas} className="px-8 py-4 bg-slate-900 dark:bg-brand-600 text-white rounded-2xl font-black text-sm uppercase tracking-widest hover:bg-slate-800 dark:hover:bg-brand-700 transition-all shadow-lg active:scale-95 flex items-center gap-3">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Atualizar"}
          </button>
        </div>

        {/* Grid de Auditoria */}
        <div className="bg-white dark:bg-slate-800 rounded-[3rem] border border-slate-100 dark:border-slate-700 shadow-2xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900 dark:bg-slate-950 text-white uppercase text-[10px] font-black tracking-[0.2em]">
                <th className="py-6 px-8">ID / Data</th>
                <th className="py-6 px-8">Mesa</th>
                <th className="py-6 px-8">Total</th>
                <th className="py-6 px-8">Pagamento</th>
                <th className="py-6 px-8 text-center">Status</th>
                <th className="py-6 px-8 text-right">Auditoria</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700 text-slate-900 dark:text-slate-200">
              {filteredVendas.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors group">
                  <td className="py-6 px-8">
                    <p className="font-black text-slate-900 dark:text-white text-sm">#{v.id}</p>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase">{new Date(v.data_abertura).toLocaleString()}</p>
                  </td>
                  <td className="py-6 px-8">
                    <span className="w-10 h-10 bg-slate-100 dark:bg-slate-900 rounded-xl flex items-center justify-center font-black text-slate-600 dark:text-slate-400">
                      {v.mesa}
                    </span>
                  </td>
                  <td className="py-6 px-8">
                    <span className="font-black text-slate-900 dark:text-white">R$ {parseFloat(v.total).toFixed(2)}</span>
                  </td>
                  <td className="py-6 px-8">
                    <span className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase bg-slate-100 dark:bg-slate-900 px-3 py-1 rounded-lg">{v.forma_pagamento || 'PENDENTE'}</span>
                  </td>
                  <td className="py-6 px-8 text-center">
                    <StatusBadge status={v.status} />
                  </td>
                  <td className="py-6 px-8 text-right">
                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button 
                        onClick={() => handleViewLog(v.id)}
                        className="p-3 bg-slate-50 dark:bg-slate-900 hover:bg-brand-600 hover:text-white text-slate-600 dark:text-slate-400 rounded-xl transition-all shadow-sm" title="Ver Logs"
                      >
                        <FileText className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => handleViewXml(v.id)}
                        className="p-3 bg-slate-50 dark:bg-slate-900 hover:bg-emerald-600 hover:text-white text-slate-600 dark:text-slate-400 rounded-xl transition-all shadow-sm" title="Ver XML"
                      >
                        <Code className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredVendas.length === 0 && !loading && (
            <div className="p-20 text-center space-y-4">
              <Clock className="w-12 h-12 text-slate-200 mx-auto" />
              <p className="text-slate-400 font-bold uppercase tracking-widest text-xs">Nenhuma venda encontrada no período.</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal de Log Rápido */}
      <AnimatePresence>
        {logView && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setLogView(null)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="relative bg-white w-full max-w-2xl rounded-[2.5rem] shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
              <div className="p-8 bg-slate-900 text-white flex items-center justify-between">
                <h3 className="text-xl font-black uppercase tracking-tight">Detalhes do Log</h3>
                <button onClick={() => setLogView(null)} className="p-2 hover:bg-white/10 rounded-full transition-all text-white"><XCircle className="w-6 h-6" /></button>
              </div>
              <div className="p-8 overflow-y-auto bg-slate-50 flex-1">
                <pre className="font-mono text-xs text-slate-600 leading-relaxed whitespace-pre-wrap bg-white p-6 rounded-2xl border border-slate-200 shadow-inner">
                  {logView}
                </pre>
              </div>
              <div className="p-6 border-t border-slate-100 flex justify-end">
                <button onClick={() => setLogView(null)} className="px-8 py-3 bg-slate-100 text-slate-600 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-slate-200 transition-all">Fechar</button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const configs: any = {
    'PAGA': { icon: <CheckCircle2 className="w-3 h-3" />, color: 'bg-emerald-50 text-emerald-600', label: 'Finalizada' },
    'AGUARDANDO_PAGAMENTO': { icon: <Clock className="w-3 h-3" />, color: 'bg-amber-50 text-amber-600', label: 'Aguardando PIX' },
    'ABERTA': { icon: <Clock className="w-3 h-3" />, color: 'bg-blue-50 text-blue-600', label: 'Em Atendimento' },
    'CANCELADA': { icon: <XCircle className="w-3 h-3" />, color: 'bg-rose-50 text-rose-600', label: 'Cancelada' },
  }
  const config = configs[status] || configs['ABERTA']
  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-[10px] font-black uppercase tracking-widest ${config.color}`}>
      {config.icon} {config.label}
    </div>
  )
}
