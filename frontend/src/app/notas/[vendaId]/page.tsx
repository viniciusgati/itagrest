'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, RefreshCcw, FileText, Code, CheckCircle2, XCircle, AlertTriangle, Loader2, Clipboard } from 'lucide-react'
import api from '@/lib/api'
import Link from 'next/link'
import { motion } from 'framer-motion'

export default function NotaFiscalDetailPage() {
  const { vendaId } = useParams()
  const router = useRouter()
  const [nota, setNota] = useState<any>(null)
  const [venda, setVenda] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [emitting, setEmitting] = useState(false)
  const [activeTab, setActiveTab] = useState<'logs' | 'xml'>('logs')

  const fetchData = async () => {
    setLoading(true)
    try {
      // Busca status da nota
      const resNota = await api.get(`/notas/status/${vendaId}`)
      setNota(resNota.data)
      
      // Busca dados da venda (opcional, para contexto)
      const resVenda = await api.get(`/vendas/lista`)
      const v = resVenda.data.find((item: any) => item.id === Number(vendaId))
      setVenda(v)
    } catch (err: any) {
      if (err.response?.status === 404) {
        setNota({ status_sefaz: 'NAO_EMITIDA', motivo_sefaz: 'Nota ainda não foi enviada para processamento.' })
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [vendaId])

  const handleEmitir = async () => {
    setEmitting(true)
    try {
      const res = await api.post(`/notas/emitir/${vendaId}`)
      setNota(res.data)
      alert("Processamento concluído! Verifique os logs.")
    } catch (err: any) {
      alert("Erro no processamento: " + (err.response?.data?.detail || err.message))
      // Atualiza para ver os logs do erro
      fetchData()
    } finally {
      setEmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Loader2 className="w-10 h-10 animate-spin text-brand-500" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-6 md:p-10 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <button onClick={() => router.back()} className="w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl flex items-center justify-center shadow-sm border border-slate-200 dark:border-slate-700 hover:bg-slate-50 transition-all">
              <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-300" />
            </button>
            <div>
              <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Gestão Fiscal</h1>
              <p className="text-slate-500 font-medium text-sm uppercase tracking-widest">Venda #{vendaId}</p>
            </div>
          </div>

          <button 
            onClick={handleEmitir}
            disabled={emitting}
            className={`px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest transition-all shadow-lg flex items-center gap-3 active:scale-95 ${
              emitting ? 'bg-slate-400 cursor-not-allowed' : 'bg-brand-600 hover:bg-brand-700 text-white'
            }`}
          >
            {emitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
            {nota?.status_sefaz === '100' ? 'Reemitir (Substituir)' : 'Emitir NFC-e Agora'}
          </button>
        </div>

        {/* Status Card */}
        <div className={`p-8 rounded-[2.5rem] border flex flex-col md:flex-row items-center gap-8 shadow-xl ${
          nota?.status_sefaz === '100' ? 'bg-emerald-50 border-emerald-100 dark:bg-emerald-950/20 dark:border-emerald-900/30' :
          nota?.status_sefaz === 'ERRO' ? 'bg-rose-50 border-rose-100 dark:bg-rose-950/20 dark:border-rose-900/30' :
          'bg-slate-100 border-slate-200 dark:bg-slate-800/50 dark:border-slate-700'
        }`}>
          <div className={`w-20 h-20 rounded-3xl flex items-center justify-center shadow-inner ${
            nota?.status_sefaz === '100' ? 'bg-emerald-500 text-white' :
            nota?.status_sefaz === 'ERRO' ? 'bg-rose-500 text-white' :
            'bg-slate-400 text-white'
          }`}>
            {nota?.status_sefaz === '100' ? <CheckCircle2 className="w-10 h-10" /> :
             nota?.status_sefaz === 'ERRO' ? <XCircle className="w-10 h-10" /> :
             <AlertTriangle className="w-10 h-10" />}
          </div>
          <div className="flex-1 text-center md:text-left">
            <h2 className="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
              {nota?.status_sefaz === '100' ? 'Nota Autorizada' : 
               nota?.status_sefaz === 'ERRO' ? 'Falha na Emissão' : 'Aguardando Envio'}
            </h2>
            <p className="text-slate-600 dark:text-slate-400 font-medium text-lg leading-tight mt-1">
              {nota?.motivo_sefaz || 'Sem informações da SEFAZ no momento.'}
            </p>
            {nota?.chave_acesso && (
              <div className="mt-4 inline-flex items-center gap-2 bg-white dark:bg-slate-800 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-[10px] font-mono font-bold text-slate-500 uppercase">
                Chave: {nota.chave_acesso}
                <button onClick={() => navigator.clipboard.writeText(nota.chave_acesso)} className="hover:text-brand-500"><Clipboard className="w-3 h-3" /></button>
              </div>
            )}
          </div>
        </div>

        {/* Auditoria Tabs */}
        <div className="bg-white dark:bg-slate-800 rounded-[3rem] border border-slate-100 dark:border-slate-700 shadow-2xl overflow-hidden flex flex-col min-h-[500px]">
          <div className="flex border-b border-slate-100 dark:border-slate-700">
            <button 
              onClick={() => setActiveTab('logs')}
              className={`flex-1 py-6 font-black text-xs uppercase tracking-widest transition-all flex items-center justify-center gap-3 ${
                activeTab === 'logs' ? 'text-brand-600 bg-slate-50/50 dark:bg-slate-900/20' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <FileText className="w-4 h-4" /> Logs de Transmissão
            </button>
            <button 
              onClick={() => setActiveTab('xml')}
              className={`flex-1 py-6 font-black text-xs uppercase tracking-widest transition-all flex items-center justify-center gap-3 ${
                activeTab === 'xml' ? 'text-emerald-600 bg-slate-50/50 dark:bg-slate-900/20' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <Code className="w-4 h-4" /> Conteúdo XML
            </button>
          </div>

          <div className="p-8 flex-1 bg-slate-50/30 dark:bg-slate-900/10 overflow-auto">
            {activeTab === 'logs' ? (
              <pre className="font-mono text-xs text-slate-600 dark:text-slate-400 leading-relaxed whitespace-pre-wrap">
                {nota?.logs_transmissao || 'Nenhum log registrado para esta operação.'}
              </pre>
            ) : (
              <div className="relative group">
                <button 
                   onClick={() => nota?.xml_autorizado && navigator.clipboard.writeText(nota.xml_autorizado)}
                   className="absolute right-4 top-4 p-3 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Clipboard className="w-4 h-4 text-slate-400" />
                </button>
                <pre className="font-mono text-[10px] text-emerald-700 dark:text-emerald-500 bg-emerald-50/30 dark:bg-emerald-950/10 p-6 rounded-3xl border border-emerald-100/50 dark:border-emerald-900/20 overflow-x-auto">
                  {nota?.xml_autorizado || 'XML não gerado ou não disponível.'}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
