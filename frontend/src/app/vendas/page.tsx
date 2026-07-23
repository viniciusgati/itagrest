'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Search, FileText, CheckCircle2, XCircle, Clock, Loader2, Printer, File, Share2, ChevronRight, Store } from 'lucide-react'
import api, { getImageUrl } from '@/lib/api'
import { motion, AnimatePresence } from 'framer-motion'

export default function VendasPage() {
  const router = useRouter()
  const [vendas, setVendas] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearch] = useState('')
  const [user, setUser] = useState<any>(null)
  const isGerente = user?.papel === 'GERENTE'

  const fetchVendas = async () => {
    setLoading(true)
    try {
      const res = await api.get('/vendas/lista')
      setVendas(res.data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    fetchVendas()
    api.get('/auth/me').then(res => setUser(res.data)).catch(() => {})
  }, [])

  const handlePrint = (vendaId: number) => {
    const token = localStorage.getItem('token')
    window.open(getImageUrl(`/api/v1/notas/${vendaId}/imprimir?token=${token}`), '_blank')
  }

  const handlePrintA4 = (vendaId: number) => {
    const token = localStorage.getItem('token')
    window.open(getImageUrl(`/api/v1/notas/${vendaId}/imprimir-a4?token=${token}`), '_blank')
  }

  const handleShare = async (vendaId: number) => {
    const token = localStorage.getItem('token')
    const baseUrl = getImageUrl('').replace(/\/api\/v1\/?$/, '')
    const url = `${baseUrl}/api/v1/notas/${vendaId}/imprimir-a4?token=${token}`
    if (navigator.share) {
      await navigator.share({ title: `DANFE Venda #${vendaId}`, url })
    } else {
      await navigator.clipboard.writeText(url)
      alert('Link da DANFE copiado! Compartilhe no WhatsApp.')
    }
  }

  const handleViewLog = (vendaId: number) => {
    router.push(`/notas/${vendaId}`)
  }

  const filteredVendas = vendas.filter(v => 
    v.id.toString().includes(searchTerm) || 
    v.mesa.toString().includes(searchTerm) ||
    v.cliente?.nome?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-4 md:p-10 font-sans transition-colors duration-300">
      <div className="max-w-5xl mx-auto space-y-6 md:space-y-10">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-black text-slate-900 dark:text-white tracking-tight">Vendas</h1>
            <p className="text-slate-400 dark:text-slate-500 font-medium text-sm">Histórico de vendas</p>
          </div>
          <button onClick={fetchVendas} disabled={loading} className="px-5 py-3 md:px-8 md:py-4 bg-slate-900 dark:bg-brand-600 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-slate-800 dark:hover:bg-brand-700 transition-all shadow-lg flex items-center gap-2 disabled:opacity-50">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Atualizar'}
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input type="text" placeholder="Buscar por Mesa, ID ou Cliente..."
            className="w-full pl-14 pr-6 py-4 bg-white dark:bg-slate-800 dark:text-white rounded-2xl border border-slate-200 dark:border-slate-700 focus:ring-4 focus:ring-brand-100 dark:focus:ring-brand-900/30 outline-none font-medium transition-all shadow-sm"
            value={searchTerm} onChange={e => setSearch(e.target.value)} />
        </div>

        {/* Card List */}
        {loading ? (
          <div className="space-y-4">
            {[1,2,3].map(i => <div key={i} className="bg-white dark:bg-slate-800 h-32 rounded-[2rem] animate-pulse border border-slate-100 dark:border-slate-700" />)}
          </div>
        ) : filteredVendas.length === 0 ? (
          <div className="bg-white dark:bg-slate-800 rounded-[3rem] p-16 text-center border border-slate-100 dark:border-slate-700 shadow-xl">
            <Store className="w-14 h-14 text-slate-200 dark:text-slate-700 mx-auto mb-4" />
            <p className="text-slate-400 dark:text-slate-500 font-bold uppercase tracking-widest text-xs">Nenhuma venda encontrada</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredVendas.map((v, idx) => (
              <motion.div
                key={v.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.03 }}
                className="bg-white dark:bg-slate-800 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-lg overflow-hidden"
              >
                {/* Card Header */}
                <div className="flex items-center justify-between p-4 md:p-6 border-b border-slate-50 dark:border-slate-700/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-xl flex items-center justify-center font-black text-slate-600 dark:text-slate-300">
                      {v.mesa}
                    </div>
                    <div>
                      <p className="font-black text-slate-900 dark:text-white text-sm leading-tight">#{v.id} · Mesa {v.mesa}</p>
                      <p className="text-[10px] text-slate-400 dark:text-slate-500 font-bold uppercase">{new Date(v.data_abertura).toLocaleString()}</p>
                    </div>
                  </div>
                  <StatusBadge status={v.status} />
                </div>

                {/* Card Body */}
                <div className="p-4 md:p-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Cliente</p>
                      <p className="font-bold text-slate-900 dark:text-white text-sm truncate">{v.cliente?.nome || 'CONSUMIDOR'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Total</p>
                      <p className="text-xl font-black text-slate-900 dark:text-white">R$ {parseFloat(v.total).toFixed(2)}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Pagamento</p>
                      <span className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase bg-slate-100 dark:bg-slate-700 px-3 py-1 rounded-lg">
                        {v.forma_pagamento || '—'}
                      </span>
                    </div>
                    {v.cliente?.documento && (
                      <p className="text-[10px] text-slate-400 font-medium">{v.cliente.documento}</p>
                    )}
                  </div>
                </div>

                {/* Card Actions */}
                <div className="flex items-center gap-2 p-4 md:p-6 bg-slate-50/50 dark:bg-slate-900/30 border-t border-slate-50 dark:border-slate-700/50 overflow-x-auto">
                  <ActionButton onClick={() => handlePrint(v.id)} icon={<Printer className="w-4 h-4" />} label="Cupom" color="hover:bg-slate-800 hover:text-white" />
                  <ActionButton onClick={() => handlePrintA4(v.id)} icon={<File className="w-4 h-4" />} label="DANFE" color="hover:bg-blue-600 hover:text-white" />
                  <ActionButton onClick={() => handleShare(v.id)} icon={<Share2 className="w-4 h-4" />} label="Compartilhar" color="hover:bg-green-600 hover:text-white" />
                  {isGerente && (
                    <ActionButton onClick={() => handleViewLog(v.id)} icon={<FileText className="w-4 h-4" />} label="Logs" color="hover:bg-brand-600 hover:text-white" />
                  )}
                  <button onClick={() => handleViewLog(v.id)} className="ml-auto p-3 text-slate-400 hover:text-brand-600 transition-colors" title="Detalhes">
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ActionButton({ onClick, icon, label, color }: { onClick: () => void; icon: React.ReactNode; label: string; color: string }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-1.5 px-4 py-2.5 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-xl text-[10px] font-black uppercase tracking-widest border border-slate-200 dark:border-slate-700 shadow-sm transition-all ${color}`}>
      {icon} {label}
    </button>
  )
}

function StatusBadge({ status }: { status: string }) {
  const configs: any = {
    'PAGA': { icon: <CheckCircle2 className="w-3 h-3" />, color: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600', label: 'Finalizada' },
    'AGUARDANDO_PAGAMENTO': { icon: <Clock className="w-3 h-3" />, color: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600', label: 'Aguardando' },
    'ABERTA': { icon: <Clock className="w-3 h-3" />, color: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600', label: 'Em Atendimento' },
    'CANCELADA': { icon: <XCircle className="w-3 h-3" />, color: 'bg-rose-50 dark:bg-rose-900/20 text-rose-600', label: 'Cancelada' },
  }
  const config = configs[status] || configs['ABERTA']
  return (
    <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest ${config.color}`}>
      {config.icon} {config.label}
    </div>
  )
}
