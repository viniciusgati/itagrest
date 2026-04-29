'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { RefreshCcw, FileText, Code, CheckCircle2, XCircle, AlertTriangle, Loader2, Clipboard, Printer, File } from 'lucide-react'
import api, { getImageUrl } from '@/lib/api'

export default function NotaFiscalDetailPage() {
  const { vendaId } = useParams()
  const router = useRouter()
  const [nota, setNota] = useState<any>(null)
  const [venda, setVenda] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [emitting, setEmitting] = useState(false)
  const [activeTab, setActiveTab] = useState<'logs' | 'xml_enviado' | 'xml_recebido' | 'xml_autorizado'>('logs')

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
      
      if (res.data.status_sefaz === '100') {
        alert("Nota Autorizada com Sucesso!")
        router.push('/vendas')
      } else {
        alert("Processamento concluído com o status: " + res.data.status_sefaz + ". Verifique os logs.")
      }
    } catch (err: any) {
      alert("Erro no processamento SEFAZ. A nota pode não ter sido emitida.")
      // Recarrega os dados para mostrar os logs do erro na tela
      fetchData()
    } finally {
      setEmitting(false)
    }
  }

  const handlePrint = () => {
    const token = localStorage.getItem('token')
    window.open(getImageUrl(`/api/v1/notas/${vendaId}/imprimir?token=${token}`), '_blank')
  }

  const handlePrintA4 = () => {
    const token = localStorage.getItem('token')
    window.open(getImageUrl(`/api/v1/notas/${vendaId}/imprimir-a4?token=${token}`), '_blank')
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
          <div>
            <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Gestão Fiscal</h1>
            <p className="text-slate-500 dark:text-slate-400 font-medium text-sm uppercase tracking-widest">Venda #{vendaId}</p>
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
          ['100', '103', '104'].includes(nota?.status_sefaz || '') ? 'bg-emerald-50 border-emerald-100 dark:bg-emerald-950/20 dark:border-emerald-900/30' :
          nota?.status_sefaz === 'ERRO' ? 'bg-rose-50 border-rose-100 dark:bg-rose-950/20 dark:border-rose-900/30' :
          'bg-slate-100 border-slate-200 dark:bg-slate-800/50 dark:border-slate-700'
        }`}>
          <div className={`w-20 h-20 rounded-3xl flex items-center justify-center shadow-inner ${
            ['100', '103', '104'].includes(nota?.status_sefaz || '') ? 'bg-emerald-500 text-white' :
            nota?.status_sefaz === 'ERRO' ? 'bg-rose-500 text-white' :
            'bg-slate-400 text-white'
          }`}>
            {['100', '103', '104'].includes(nota?.status_sefaz || '') ? <CheckCircle2 className="w-10 h-10" /> :
             nota?.status_sefaz === 'ERRO' ? <XCircle className="w-10 h-10" /> :
             <AlertTriangle className="w-10 h-10" />}
          </div>
          <div className="flex-1 text-center md:text-left">
            <h2 className="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
              {['100', '103', '104'].includes(nota?.status_sefaz || '') ? 'Nota Emitida' : 
               nota?.status_sefaz === 'ERRO' ? 'Falha na Emissão' : 'Aguardando Envio'}
            </h2>
            <p className="text-slate-600 dark:text-slate-400 font-medium text-lg leading-tight mt-1">
              {nota?.motivo_sefaz || 'Sem informações da SEFAZ no momento.'}
            </p>
            {nota?.chave_acesso && (
              <div className="flex flex-col gap-4">
                <div className="inline-flex items-center gap-2 bg-white dark:bg-slate-800 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-[10px] font-mono font-bold text-slate-500 uppercase">
                  Chave: {nota.chave_acesso}
                  <button onClick={() => navigator.clipboard.writeText(nota.chave_acesso)} className="hover:text-brand-500"><Clipboard className="w-3 h-3" /></button>
                </div>
                
                <div className="flex items-center gap-3">
                  <button 
                    onClick={handlePrint}
                    className="flex-1 px-6 py-3 bg-slate-900 dark:bg-slate-700 text-white rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-slate-800 transition-all flex items-center justify-center gap-2 shadow-lg"
                  >
                    <Printer className="w-4 h-4" /> Cupom 80mm
                  </button>
                  <button 
                    onClick={handlePrintA4}
                    className="flex-1 px-6 py-3 bg-blue-600 dark:bg-blue-700 text-white rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-lg"
                  >
                    <File className="w-4 h-4" /> DANFE A4
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Auditoria Tabs */}
        <div className="bg-white dark:bg-slate-800 rounded-[3rem] border border-slate-100 dark:border-slate-700 shadow-2xl overflow-hidden flex flex-col min-h-[500px]">
          <div className="flex border-b border-slate-100 dark:border-slate-700 overflow-x-auto">
            {[
              { id: 'logs', label: 'Logs', icon: FileText, color: 'text-brand-600' },
              { id: 'xml_enviado', label: 'XML Envio', icon: Code, color: 'text-blue-600' },
              { id: 'xml_recebido', label: 'XML Recebido', icon: Code, color: 'text-amber-600' },
              { id: 'xml_autorizado', label: 'XML Autorizado', icon: Code, color: 'text-emerald-600' },
            ].map((tab) => (
              <button 
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex-1 min-w-[120px] py-6 font-black text-[10px] uppercase tracking-widest transition-all flex items-center justify-center gap-2 ${
                  activeTab === tab.id ? `${tab.color} bg-slate-50/50 dark:bg-slate-900/20` : 'text-slate-400 hover:text-slate-600'
                }`}
              >
                <tab.icon className="w-3 h-3" /> {tab.label}
              </button>
            ))}
          </div>

          <div className="p-8 flex-1 bg-slate-50/30 dark:bg-slate-900/10 overflow-auto">
            {activeTab === 'logs' ? (
              <pre className="font-mono text-xs text-slate-600 dark:text-slate-400 leading-relaxed whitespace-pre-wrap">
                {nota?.logs_transmissao || 'Nenhum log registrado para esta operação.'}
              </pre>
            ) : (
              <div className="relative group">
                <button 
                   onClick={() => {
                     const content = activeTab === 'xml_enviado' ? nota?.xml_enviado : 
                                    activeTab === 'xml_recebido' ? nota?.xml_recebido : 
                                    nota?.xml_autorizado;
                     if (content) navigator.clipboard.writeText(content);
                   }}
                   className="absolute right-4 top-4 p-3 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Clipboard className="w-4 h-4 text-slate-400" />
                </button>
                <pre className={`font-mono text-[10px] p-6 rounded-3xl border overflow-x-auto ${
                  activeTab === 'xml_enviado' ? 'text-blue-700 dark:text-blue-500 bg-blue-50/30 dark:bg-blue-950/10 border-blue-100/50' :
                  activeTab === 'xml_recebido' ? 'text-amber-700 dark:text-amber-500 bg-amber-50/30 dark:bg-amber-950/10 border-amber-100/50' :
                  'text-emerald-700 dark:text-emerald-500 bg-emerald-50/30 dark:bg-emerald-950/10 border-emerald-100/50'
                }`}>
                  {activeTab === 'xml_enviado' ? (nota?.xml_enviado || 'XML de envio não disponível.') : 
                   activeTab === 'xml_recebido' ? (nota?.xml_recebido || 'XML de recebimento (bruto) não disponível.') : 
                   (nota?.xml_autorizado || 'XML autorizado (nfeProc) não disponível.')}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
