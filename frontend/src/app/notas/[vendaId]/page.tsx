'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { RefreshCcw, FileText, Code, CheckCircle2, XCircle, AlertTriangle, Loader2, Clipboard, Printer, File, Share2, Ban } from 'lucide-react'
import api, { getImageUrl } from '@/lib/api'
import { vendaService } from '@/services/venda.service'

export default function NotaFiscalDetailPage() {
  const { vendaId } = useParams()
  const router = useRouter()
  const [nota, setNota] = useState<any>(null)
  const [venda, setVenda] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [emitting, setEmitting] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [justificativa, setJustificativa] = useState('')
  const [activeTab, setActiveTab] = useState<'logs' | 'xml_enviado' | 'xml_recebido' | 'xml_autorizado'>('logs')

  const isAuthorized = nota?.status_sefaz === '100'
  const isCanceled = !!nota?.protocolo_cancelamento

  const fetchData = async () => {
    setLoading(true)
    try {
      const resNota = await api.get(`/notas/status/${vendaId}`)
      setNota(resNota.data)
      
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
      fetchData()
    } finally {
      setEmitting(false)
    }
  }

  const handleCancelar = async () => {
    if (justificativa.trim().length < 15) {
      alert("Justificativa deve ter no mínimo 15 caracteres.")
      return
    }
    setCancelling(true)
    try {
      const res = await vendaService.cancelarNota(Number(vendaId), justificativa.trim())
      setNota(res)
      setShowCancelModal(false)
      setJustificativa('')
      if (res.status_sefaz === 'CANCELADA') {
        alert("Nota cancelada com sucesso!")
      } else {
        alert("Falha no cancelamento: " + (res.motivo_sefaz || 'Erro desconhecido'))
      }
    } catch (err: any) {
      alert("Erro ao cancelar nota: " + (err.response?.data?.detail || err.message))
      fetchData()
    } finally {
      setCancelling(false)
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

  const getStatusConfig = () => {
    if (isCanceled) return {
      bg: 'bg-red-50 border-red-100 dark:bg-red-950/20 dark:border-red-900/30',
      icon: 'bg-red-500 text-white',
      Icon: XCircle,
      title: 'Nota Cancelada',
    }
    if (['100', '103', '104'].includes(nota?.status_sefaz || '')) return {
      bg: 'bg-emerald-50 border-emerald-100 dark:bg-emerald-950/20 dark:border-emerald-900/30',
      icon: 'bg-emerald-500 text-white',
      Icon: CheckCircle2,
      title: 'Nota Emitida',
    }
    if (nota?.status_sefaz === 'ERRO') return {
      bg: 'bg-rose-50 border-rose-100 dark:bg-rose-950/20 dark:border-rose-900/30',
      icon: 'bg-rose-500 text-white',
      Icon: XCircle,
      title: 'Falha na Emissão',
    }
    return {
      bg: 'bg-slate-100 border-slate-200 dark:bg-slate-800/50 dark:border-slate-700',
      icon: 'bg-slate-400 text-white',
      Icon: AlertTriangle,
      title: 'Aguardando Envio',
    }
  }

  const MOTIVOS_CANCELAMENTO = [
    { label: 'Arrependimento do consumidor', value: 'Arrependimento do consumidor' },
    { label: 'Erro na emissão da nota fiscal', value: 'Erro na emissão da nota fiscal' },
    { label: 'Venda cancelada pelo cliente', value: 'Venda cancelada pelo cliente' },
    { label: 'Erro no valor total da venda', value: 'Erro no valor total da venda' },
    { label: 'Desistência da compra realizada', value: 'Desistência da compra realizada' },
    { label: 'Erro no CPF/CNPJ do cliente', value: 'Erro no CPF/CNPJ do cliente' },
    { label: 'Erro de digitação na emissão', value: 'Erro de digitação na emissão' },
    { label: 'Outro (digitar manualmente)', value: '' },
  ]

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Loader2 className="w-10 h-10 animate-spin text-brand-500" />
      </div>
    )
  }

  const statusCfg = getStatusConfig()

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-6 md:p-10 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Gestão Fiscal</h1>
            <p className="text-slate-500 dark:text-slate-400 font-medium text-sm uppercase tracking-widest">Venda #{vendaId}</p>
          </div>

          <div className="flex gap-3">
            {!isAuthorized && !isCanceled && (
              <button 
                onClick={handleEmitir}
                disabled={emitting}
                className={`px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest transition-all shadow-lg flex items-center gap-3 active:scale-95 ${
                  emitting ? 'bg-slate-400 cursor-not-allowed' : 'bg-brand-600 hover:bg-brand-700 text-white'
                }`}
              >
                {emitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCcw className="w-4 h-4" />}
                Emitir NFC-e Agora
              </button>
            )}
            {isAuthorized && !isCanceled && (
              <button 
                onClick={() => setShowCancelModal(true)}
                className="px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest transition-all shadow-lg flex items-center gap-3 active:scale-95 bg-red-600 hover:bg-red-700 text-white"
              >
                <Ban className="w-4 h-4" />
                Cancelar NFC-e
              </button>
            )}
          </div>
        </div>

        {/* Status Card */}
        <div className={`p-8 rounded-[2.5rem] border flex flex-col md:flex-row items-center gap-8 shadow-xl ${statusCfg.bg}`}>
          <div className={`w-20 h-20 rounded-3xl flex items-center justify-center shadow-inner ${statusCfg.icon}`}>
            <statusCfg.Icon className="w-10 h-10" />
          </div>
          <div className="flex-1 text-center md:text-left">
            <h2 className="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight">{statusCfg.title}</h2>
            <p className="text-slate-600 dark:text-slate-400 font-medium text-lg leading-tight mt-1">
              {isCanceled ? (nota?.motivo_cancelamento || 'Cancelamento homologado') : (nota?.motivo_sefaz || 'Sem informações da SEFAZ no momento.')}
            </p>
            {isCanceled && nota?.protocolo_cancelamento && (
              <p className="text-sm font-mono text-slate-500 dark:text-slate-400 mt-2">
                Protocolo de Cancelamento: {nota.protocolo_cancelamento}
              </p>
            )}
            {nota?.chave_acesso && (
              <div className="flex flex-col gap-4 mt-4">
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
                  <button 
                    onClick={() => {
                      const token = localStorage.getItem('token')
                      const url = `${window.location.origin}/api/v1/notas/${vendaId}/imprimir-a4?token=${token}`
                      if (navigator.share) {
                        navigator.share({ title: `DANFE Venda #${vendaId}`, url })
                      } else {
                        navigator.clipboard.writeText(url)
                        alert('Link da DANFE copiado!')
                      }
                    }}
                    className="flex-1 px-6 py-3 bg-emerald-600 dark:bg-emerald-700 text-white rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-emerald-700 transition-all flex items-center justify-center gap-2 shadow-lg"
                  >
                    <Share2 className="w-4 h-4" /> Compartilhar
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

      {/* Cancel Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-[2rem] shadow-2xl max-w-lg w-full p-8 space-y-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <Ban className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <h3 className="text-xl font-black text-slate-900 dark:text-white">Cancelar NFC-e</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">Esta ação não pode ser desfeita.</p>
              </div>
            </div>

            <div>
              <label className="block text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-2">
                Motivo do cancelamento
              </label>
              <select
                onChange={(e) => setJustificativa(e.target.value)}
                value={MOTIVOS_CANCELAMENTO.some(m => m.value === justificativa) ? justificativa : ''}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm font-medium focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none mb-3"
              >
                <option value="">Selecione um motivo...</option>
                {MOTIVOS_CANCELAMENTO.map((m) => (
                  <option key={m.label} value={m.value}>{m.label}</option>
                ))}
              </select>
              <textarea
                value={justificativa}
                onChange={(e) => setJustificativa(e.target.value)}
                rows={3}
                maxLength={255}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm font-medium focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none resize-none"
                placeholder="Descreva o motivo do cancelamento..."
              />
              <p className="text-xs text-slate-400 mt-1">
                {justificativa.length}/255
                {justificativa.length > 0 && justificativa.length < 15 && (
                  <span className="text-red-500 ml-2">mínimo 15 caracteres</span>
                )}
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => { setShowCancelModal(false); setJustificativa('') }}
                className="flex-1 px-6 py-3 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold text-sm hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
              >
                Voltar
              </button>
              <button
                onClick={handleCancelar}
                disabled={cancelling || justificativa.trim().length < 15}
                className="flex-1 px-6 py-3 rounded-xl bg-red-600 hover:bg-red-700 disabled:bg-slate-400 text-white font-bold text-sm transition-all flex items-center justify-center gap-2"
              >
                {cancelling ? <Loader2 className="w-4 h-4 animate-spin" /> : <Ban className="w-4 h-4" />}
                Confirmar Cancelamento
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}