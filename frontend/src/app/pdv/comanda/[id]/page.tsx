'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { 
  ArrowLeft, Search, Plus, Trash2, 
  CreditCard, X, Check, Loader2, DollarSign, 
  QrCode, Utensils, ShoppingBag, User, UserPlus, Printer, FileText
} from 'lucide-react'
import api, { getImageUrl } from '@/lib/api'
import { motion, AnimatePresence } from 'framer-motion'
import { QRCodeSVG } from 'qrcode.react'

export default function ComandaMobilePage() {
  const { id } = useParams()
  const router = useRouter()
  const [venda, setVenda] = useState<any>(null)
  const [produtos, setProdutos] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCheckout, setShowCheckout] = useState(false)
  const [checkoutStep, setCheckoutStep] = useState<'summary' | 'payment'>('summary')
  const [showAddItems, setShowAddItems] = useState(false)
  const [isEmitting, setIsEmitting] = useState(false)
  const [fiscalStatus, setFiscalStatus] = useState<any>(null)
  const [error, setError] = useState('')

  const [showClienteSearch, setShowClienteSearch] = useState(false)
  const [showNomeSearch, setShowNomeSearch] = useState(false)
  const [clienteDoc, setClienteDoc] = useState('')
  const [nomeQuery, setNomeQuery] = useState('')
  const [sugestoes, setSugestoes] = useState<any[]>([])
  const [clienteEncontrado, setClienteEncontrado] = useState<any>(null)
  const [isSearchingCliente, setIsSearchingCliente] = useState(false)
  const [justLinked, setJustLinked] = useState(false)
  const [importingPdf, setImportingPdf] = useState(false)
  const pdfFileRef = useRef<HTMLInputElement>(null)

  // Auto-complete de Clientes por Nome
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (nomeQuery.length >= 2) {
        try {
          const res = await api.get(`/clientes/pesquisar/termo?q=${nomeQuery}`)
          setSugestoes(res.data)
        } catch (err) { console.error(err) }
      } else {
        setSugestoes([])
      }
    }, 300)

    return () => clearTimeout(delayDebounceFn)
  }, [nomeQuery])
  const [addingItem, setAddingItem] = useState<number | null>(null)
  const [justAdded, setJustAdded] = useState<number | null>(null)

  const fetchVenda = async () => {
    try {
      const res = await api.post('/vendas', { mesa: parseInt(id as string) })
      setVenda(res.data)
      // Sincronizar o cliente encontrado com o que veio do banco
      if (res.data.cliente) {
        setClienteEncontrado(res.data.cliente)
      } else {
        setClienteEncontrado(null)
      }
    } catch (err) { console.error(err) }
  }

  const fetchProdutos = async () => {
    try {
      const res = await api.get('/produtos')
      setProdutos(res.data)
    } catch (err) { console.error(err) }
  }

  useEffect(() => {
    Promise.all([fetchVenda(), fetchProdutos()]).finally(() => setLoading(false))
  }, [id])

  const handleAddItem = async (produto: any) => {
    if (!venda?.id || addingItem) return
    setAddingItem(produto.id)
    try {
      const res = await api.post(`/vendas/${venda.id}/itens`, {
        produto_id: produto.id,
        quantidade: 1
      })
      setVenda(res.data)
      setJustAdded(produto.id)
      setTimeout(() => setJustAdded(null), 1500) // Feedback visual por 1.5s
    } catch (err) { 
      console.error(err) 
    } finally {
      setAddingItem(null)
    }
  }

  const getItemCount = (produtoId: number) => {
    return venda?.itens?.filter((i: any) => i.produto_id === produtoId).length || 0
  }

  const handleRemoveItem = async (ids: number[]) => {
    const lastId = ids[ids.length - 1]
    try {
      const res = await api.delete(`/vendas/${venda.id}/itens/${lastId}`)
      setVenda(res.data)
    } catch (err) { console.error(err) }
  }

  const handleVincularCliente = async (clienteId?: number, clienteObj?: any) => {
    if (!clienteId && (!clienteDoc || isSearchingCliente)) return
    setIsSearchingCliente(true)
    try {
      let finalCliente = clienteObj
      
      if (!clienteId) {
        // Busca por documento se não foi passado um ID direto (auto-complete)
        const cleanDoc = clienteDoc.replace(/\D/g, '')
        const res = await api.get(`/clientes/buscar-doc/${cleanDoc}`)
        finalCliente = res.data
      }
      
      await api.put(`/vendas/${venda.id}/fechar`, { cliente_id: finalCliente.id })
      
      setClienteEncontrado(finalCliente)
      setJustLinked(true)
      
      // Pequeno delay para mostrar o sucesso antes de fechar o modal
      setTimeout(() => {
        setJustLinked(false)
        setShowClienteSearch(false)
        setShowNomeSearch(false)
        fetchVenda()
        setClienteDoc('')
        setNomeQuery('')
        setSugestoes([])
      }, 1500)
    } catch (err) {
      alert("Cliente não encontrado. Cadastre-o primeiro.")
    } finally {
      setIsSearchingCliente(false)
    }
  }

  const handleImportPdf = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImportingPdf(true)
    try {
      // 1. Extrair dados do PDF
      const fd = new FormData()
      fd.append('file', file)
      const parsed = await api.post('/clientes/extrair-cnpj-pdf', fd)
      const d = parsed.data

      // 2. Criar cliente
      const newClient = await api.post('/clientes', {
        nome: d.razao_social || d.nome_fantasia || 'Cliente',
        documento: d.cnpj,
        email: d.email || '',
        telefone: d.telefone || '',
        logradouro: d.logradouro || '',
        numero: d.numero || '',
        bairro: d.bairro || '',
        municipio_nome: d.municipio || '',
        uf: d.uf || '',
      })
      const cliente = newClient.data

      // 3. Vincular à venda
      await api.put(`/vendas/${venda.id}/fechar`, { cliente_id: cliente.id })

      setClienteEncontrado(cliente)
      setJustLinked(true)
      setTimeout(() => {
        setJustLinked(false)
        setShowClienteSearch(false)
        fetchVenda()
      }, 1500)
    } catch (err: any) {
      alert(err.response?.data?.detail || "Erro ao importar Cartão CNPJ")
    } finally {
      setImportingPdf(false)
      if (pdfFileRef.current) pdfFileRef.current.value = ''
    }
  }

  const handleFecharMesa = async (forma: string) => {
    setIsEmitting(true)
    setError('')
    try {
      // 1. Primeiro garante o fechamento da venda no banco (independente da nota)
      const res = await api.put(`/vendas/${venda.id}/fechar`, {
        forma_pagamento: forma,
        status: forma === 'PIX' ? 'AGUARDANDO_PAGAMENTO' : 'PAGA'
      })
      setVenda(res.data)
      
      // 2. Tenta emitir a nota se for dinheiro (fluxo automático)
      if (forma === 'DINHEIRO') {
        const resNota = await api.post(`/notas/emitir/${venda.id}`)
        setFiscalStatus(resNota.data)
      } else {
        // Se for PIX ou outro, apenas fecha o modal e volta pro mapa
        router.push('/pdv')
      }
    } catch (err: any) {
      console.error("Erro no fechamento:", err)
      const detail = err.response?.data?.detail
      setError(detail || "Falha ao fechar mesa. Verifique a conexão.")
    } finally { 
      setIsEmitting(false) 
    }
  }

  const getItensAgrupados = () => {
    if (!venda?.itens) return []
    const grupos: any = {}
    venda.itens.forEach((item: any) => {
      const pid = item.produto_id
      if (!grupos[pid]) {
        grupos[pid] = { ...item, ids_originais: [item.id], quantidade: parseFloat(item.quantidade), subtotal: parseFloat(item.subtotal) }
      } else {
        grupos[pid].quantidade += parseFloat(item.quantidade)
        grupos[pid].subtotal += parseFloat(item.subtotal)
        grupos[pid].ids_originais.push(item.id)
      }
    })
    return Object.values(grupos)
  }

  if (loading) return <div className="min-h-screen bg-slate-100 dark:bg-slate-900 flex items-center justify-center"><Loader2 className="animate-spin w-8 h-8 text-brand-600" /></div>

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 flex flex-col font-sans transition-colors duration-300">
      
      <div className="sticky top-0 z-40 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-5 flex items-center justify-between shadow-sm">
        <button onClick={() => router.push('/pdv')} className="p-2 -ml-2 text-slate-400"><ArrowLeft className="w-6 h-6" /></button>
        <div className="text-center">
          <h1 className="font-black text-slate-900 dark:text-white uppercase tracking-tighter text-xl">Mesa {id}</h1>
          <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">{venda?.status}</p>
        </div>
        <button onClick={() => setShowClienteSearch(true)} className="flex items-center gap-2">
          {clienteEncontrado && (
            <div className="text-right hidden sm:block">
              <p className="text-[9px] font-black text-brand-600 uppercase leading-none">Cliente</p>
              <p className="text-[11px] font-bold text-slate-900 dark:text-white max-w-[80px] truncate leading-tight">{clienteEncontrado.nome}</p>
            </div>
          )}
          <div className={`p-3 rounded-xl transition-all duration-300 ${clienteEncontrado ? 'bg-brand-50 dark:bg-brand-900/20 text-brand-600' : 'text-slate-300'}`}>
            <User className="w-6 h-6" />
          </div>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 pb-32">
        {clienteEncontrado && (
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="bg-brand-50 dark:bg-brand-900/10 border border-brand-100 dark:border-brand-900/20 p-4 rounded-3xl flex items-center gap-4">
            <div className="w-10 h-10 bg-brand-600 text-white rounded-full flex items-center justify-center font-black">
              {clienteEncontrado.nome.charAt(0)}
            </div>
            <div>
              <p className="text-[10px] font-black text-brand-600 uppercase tracking-widest">Cliente Associado</p>
              <p className="text-sm font-black text-slate-900 dark:text-white">{clienteEncontrado.nome}</p>
            </div>
          </motion.div>
        )}

        {getItensAgrupados().map((item: any) => (
          <motion.div layout key={item.produto_id} className="bg-white dark:bg-slate-800 p-5 rounded-[2rem] flex items-center justify-between shadow-sm border border-slate-50 dark:border-slate-700/50">
            <div className="flex-1">
              <h4 className="font-black text-slate-900 dark:text-white leading-tight">{item.produto.descricao}</h4>
              <p className="text-[11px] text-slate-400 font-bold uppercase mt-1">{item.quantidade}x R$ {parseFloat(item.preco_unitario).toFixed(2)}</p>
            </div>
            <div className="flex items-center gap-5">
              <span className="font-black text-slate-900 dark:text-white text-lg">R$ {item.subtotal.toFixed(2)}</span>
              <button onClick={() => handleRemoveItem(item.ids_originais)} className="p-3 bg-rose-50 dark:bg-rose-900/20 text-rose-500 rounded-2xl"><Trash2 className="w-4 h-4" /></button>
            </div>
          </motion.div>
        ))}
        {venda?.itens?.length === 0 && <div className="py-24 text-center"><ShoppingBag className="w-10 h-10 text-slate-200 mx-auto mb-4" /><p className="text-slate-400 font-bold uppercase text-xs">Mesa vazia.</p></div>}
      </div>

      <motion.button onClick={() => setShowAddItems(true)} className="fixed bottom-48 right-6 w-16 h-16 bg-brand-600 text-white rounded-2xl shadow-2xl flex items-center justify-center z-40"><Plus className="w-8 h-8" /></motion.button>

      <div className="fixed bottom-0 inset-x-0 bg-white dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 p-6 flex flex-col gap-4 shadow-2xl rounded-t-[3rem] z-30">
        <div className="flex items-center justify-between px-4"><span className="text-slate-400 font-black uppercase text-xs">Total</span><span className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">R$ {parseFloat(venda?.total || "0").toFixed(2)}</span></div>
        <button 
          disabled={!venda?.itens?.length} 
          onClick={() => { setCheckoutStep('summary'); setShowCheckout(true); }} 
          className="w-full bg-slate-900 dark:bg-brand-600 text-white font-black py-5 rounded-[1.5rem] shadow-xl flex items-center justify-center gap-3 active:scale-95 transition-transform"
        >
          <Check className="w-5 h-5" /> FECHAR CONTA
        </button>
      </div>

      {/* Modais omitidos mas preservados no fluxo Real */}
      <AnimatePresence>
        {showAddItems && (
          <motion.div initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }} className="fixed inset-0 z-50 bg-white dark:bg-slate-900 flex flex-col p-6">
            <div className="flex justify-between mb-6"><h2 className="text-xl font-black dark:text-white uppercase">Cardápio</h2><button onClick={() => setShowAddItems(false)} className="p-2 bg-slate-100 dark:bg-slate-800 rounded-full"><X /></button></div>
            <div className="grid grid-cols-2 gap-4 flex-1 overflow-y-auto">
              {produtos.map(p => {
                const count = getItemCount(p.id)
                const isAdding = addingItem === p.id
                const isJustAdded = justAdded === p.id

                return (
                  <button 
                    key={p.id} 
                    disabled={isAdding}
                    onClick={() => handleAddItem(p)} 
                    className={`bg-white dark:bg-slate-800 p-4 rounded-3xl border-2 text-left active:scale-95 transition-all relative overflow-hidden flex flex-col min-h-[160px] ${
                      isJustAdded ? 'border-emerald-500 shadow-lg shadow-emerald-500/20' : 'border-slate-100 dark:border-slate-700'
                    }`}
                  >
                    {count > 0 && (
                      <div className="absolute top-2 right-2 bg-brand-600 text-white text-[10px] font-black px-2 py-0.5 rounded-full z-10 animate-in zoom-in">
                        {count}
                      </div>
                    )}
                    
                    <div className="h-24 w-full bg-slate-50 dark:bg-slate-900 rounded-xl mb-2 overflow-hidden relative flex-shrink-0">
                      {p.imagem_url && <img src={getImageUrl(p.imagem_url)} className="w-full h-full object-cover" alt={p.descricao} />}
                      {isAdding && (
                        <div className="absolute inset-0 bg-white/60 dark:bg-slate-900/60 flex items-center justify-center">
                          <Loader2 className="w-6 h-6 animate-spin text-brand-600" />
                        </div>
                      )}
                      {isJustAdded && (
                        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute inset-0 bg-emerald-500/20 flex items-center justify-center">
                          <div className="bg-emerald-500 text-white rounded-full p-1 shadow-lg">
                            <Check className="w-6 h-6" />
                          </div>
                        </motion.div>
                      )}
                    </div>
                    
                    <div className="flex-1 flex flex-col justify-between">
                      <h4 className="text-[11px] font-black dark:text-white leading-tight line-clamp-2">{p.descricao}</h4>
                      <p className="text-brand-600 font-black text-sm mt-1">R$ {parseFloat(p.preco_venda).toFixed(2)}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showCheckout && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 bg-slate-900/95 backdrop-blur-2xl p-6 flex flex-col justify-center">
            <div className="bg-white dark:bg-slate-800 rounded-[3rem] p-8 max-h-[90vh] flex flex-col shadow-2xl relative overflow-hidden">
              <button onClick={() => setShowCheckout(false)} className="absolute top-6 right-6 p-2 text-slate-300 z-10"><X /></button>
              
              <div className="text-center mb-6">
                <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase">
                  {isEmitting ? 'Emitindo Nota' : fiscalStatus ? 'Status Fiscal' : checkoutStep === 'summary' ? 'Resumo da Conta' : 'Pagamento'}
                </h2>
              </div>

              {isEmitting ? (
                <div className="py-20 text-center space-y-6"><Loader2 className="w-16 h-16 text-brand-600 animate-spin mx-auto" /><p className="font-black dark:text-white uppercase tracking-widest text-xs">Comunicando SEFAZ...</p></div>
              ) : fiscalStatus ? (
                <div className="py-10 text-center space-y-6 overflow-y-auto">
                  {fiscalStatus.status_sefaz === '100' ? (
                    <>
                      <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 mx-auto"><Check className="w-10 h-10" /></div>
                      <p className="text-xl font-black text-emerald-600 uppercase">Autorizada!</p>
                      <button 
                        onClick={() => { 
                          const token = localStorage.getItem('token');
                          window.open(getImageUrl(`/api/v1/notas/${venda.id}/imprimir?token=${token}`), '_blank'); 
                          router.push('/pdv') 
                        }}
                        className="w-full mt-4 bg-slate-900 dark:bg-brand-600 text-white py-4 rounded-2xl font-black uppercase tracking-widest text-xs flex items-center justify-center gap-3"
                      >
                        <Printer className="w-5 h-5" /> Imprimir Cupom
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="w-20 h-20 bg-rose-100 rounded-full flex items-center justify-center text-rose-600 mx-auto"><X className="w-10 h-10" /></div>
                      <p className="text-xl font-black text-rose-600 uppercase">Falha na Nota</p>
                      <p className="text-slate-500 text-xs font-medium px-4">{fiscalStatus.motivo_sefaz || "Erro desconhecido na SEFAZ"}</p>
                      <div className="grid grid-cols-2 gap-4 mt-6">
                        <button 
                          onClick={() => router.push(`/notas/${venda.id}`)}
                          className="bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white py-4 rounded-2xl font-black uppercase tracking-widest text-[10px] flex items-center justify-center gap-2"
                        >
                          <FileText className="w-4 h-4" /> Detalhes/Logs
                        </button>
                        <button 
                          onClick={() => router.push('/pdv')}
                          className="bg-slate-900 dark:bg-brand-600 text-white py-4 rounded-2xl font-black uppercase tracking-widest text-[10px]"
                        >
                          Mapa de Mesas
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : checkoutStep === 'summary' ? (
                <div className="flex-1 flex flex-col min-h-0">
                  <div className="flex-1 overflow-y-auto pr-2 space-y-4 mb-6">
                    {/* Badge do Cliente no Resumo */}
                    <div className={`p-4 rounded-2xl flex items-center gap-4 border transition-colors ${clienteEncontrado ? 'bg-brand-50/50 border-brand-100 dark:bg-brand-900/10 dark:border-brand-900/20' : 'bg-slate-50 border-slate-100 dark:bg-slate-900/30 dark:border-slate-700'}`}>
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-black ${clienteEncontrado ? 'bg-brand-600' : 'bg-slate-400'}`}>
                        {clienteEncontrado ? clienteEncontrado.nome.charAt(0) : <User className="w-5 h-5" />}
                      </div>
                      <div className="flex-1">
                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Destinatário</p>
                        <p className="text-sm font-black dark:text-white">{clienteEncontrado ? clienteEncontrado.nome : 'Consumidor Final'}</p>
                      </div>
                      {!clienteEncontrado && (
                        <button 
                          onClick={() => { setShowCheckout(false); setShowClienteSearch(true); }}
                          className="text-[10px] font-black text-brand-600 uppercase underline"
                        >
                          Identificar
                        </button>
                      )}
                    </div>

                    {/* Lista de Itens no Resumo */}
                    <div className="space-y-3">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-2">Itens da Comanda</p>
                      {getItensAgrupados().map((item: any) => (
                        <div key={item.produto_id} className="flex justify-between items-center px-2 py-1 border-b border-slate-50 dark:border-slate-700/50">
                          <div>
                            <p className="text-xs font-bold dark:text-white leading-tight">{item.produto.descricao}</p>
                            <p className="text-[10px] text-slate-400 font-bold uppercase">{item.quantidade}x R$ {parseFloat(item.preco_unitario).toFixed(2)}</p>
                          </div>
                          <p className="text-sm font-black dark:text-white">R$ {item.subtotal.toFixed(2)}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-6 border-t border-slate-100 dark:border-slate-700 space-y-4">
                    <div className="flex items-center justify-between px-2">
                      <span className="text-slate-400 font-black uppercase text-xs">Total a pagar</span>
                      <span className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">R$ {parseFloat(venda?.total || "0").toFixed(2)}</span>
                    </div>
                    <button 
                      disabled={!venda?.itens?.length || parseFloat(venda?.total || "0") <= 0}
                      onClick={() => setCheckoutStep('payment')}
                      className="w-full bg-slate-900 dark:bg-brand-600 text-white py-5 rounded-2xl font-black uppercase tracking-widest text-xs shadow-xl active:scale-95 transition-transform disabled:opacity-50 disabled:grayscale"
                    >
                      Confirmar e Ir para Pagamento
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 py-4">
                  <div className="flex items-center justify-between px-4 mb-4">
                    <span className="text-slate-400 font-black uppercase text-xs">Total</span>
                    <span className="text-2xl font-black text-slate-900 dark:text-white tracking-tighter">R$ {parseFloat(venda?.total || "0").toFixed(2)}</span>
                  </div>
                  <div className="grid grid-cols-1 gap-4">
                    <button onClick={() => handleFecharMesa('DINHEIRO')} className="h-28 bg-emerald-600 text-white rounded-[2.5rem] flex items-center justify-center gap-6 font-black uppercase shadow-lg active:scale-95 transition-transform"><DollarSign className="w-8 h-8" /> Dinheiro</button>
                    <button onClick={() => handleFecharMesa('PIX')} className="h-24 bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-white rounded-[2.5rem] flex items-center justify-center gap-4 font-black uppercase active:scale-95 transition-transform"><QrCode className="w-6 h-6 text-brand-600" /> PIX</button>
                  </div>
                  <button onClick={() => setCheckoutStep('summary')} className="w-full py-2 text-slate-400 font-bold text-[10px] uppercase tracking-widest">Voltar ao Resumo</button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showClienteSearch && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => !isSearchingCliente && setShowClienteSearch(false)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="relative bg-white dark:bg-slate-800 w-full max-w-md rounded-[2.5rem] shadow-2xl p-8 space-y-6">
               <div className="text-center">
                 <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 transition-colors duration-500 ${justLinked ? 'bg-emerald-500 text-white' : 'bg-brand-50 text-brand-600'}`}>
                   {justLinked ? <Check className="w-8 h-8" /> : <UserPlus className="w-8 h-8" />}
                 </div>
                 <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
                   {justLinked ? 'Cliente Vinculado!' : 'Identificar Cliente'}
                 </h3>
                 <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">
                   {justLinked ? clienteEncontrado?.nome : 'Informe o CPF ou CNPJ'}
                 </p>
               </div>

               <div className="relative">
                 <input 
                  type="text" 
                  disabled={isSearchingCliente || justLinked}
                  placeholder="000.000.000-00" 
                  className="w-full px-6 py-5 bg-slate-50 dark:bg-slate-900 dark:text-white rounded-2xl outline-none font-black text-center text-lg placeholder:text-slate-300 transition-all focus:ring-4 focus:ring-brand-500/10" 
                  value={clienteDoc} 
                  onChange={e => setClienteDoc(e.target.value)} 
                  onKeyDown={e => e.key === 'Enter' && handleVincularCliente()}
                 />
               </div>

               <div className="flex flex-col gap-3">
                 <button 
                  disabled={!clienteDoc || isSearchingCliente || justLinked}
                  onClick={() => handleVincularCliente()} 
                  className={`w-full py-5 rounded-2xl font-black uppercase tracking-widest text-xs flex items-center justify-center gap-3 transition-all duration-300 shadow-xl ${
                    justLinked ? 'bg-emerald-500 text-white' : 'bg-slate-900 dark:bg-brand-600 text-white active:scale-95'
                  }`}
                 >
                   {isSearchingCliente ? (
                     <Loader2 className="w-5 h-5 animate-spin" />
                   ) : justLinked ? (
                     <Check className="w-5 h-5" />
                   ) : (
                     'Vincular por Documento'
                   )}
                 </button>
                 
                  {!justLinked && (
                    <button 
                     onClick={() => { setShowClienteSearch(false); setShowNomeSearch(true); }}
                     className="w-full py-4 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-2xl font-black uppercase tracking-widest text-[10px] flex items-center justify-center gap-2"
                    >
                      <Search className="w-4 h-4" /> Buscar por Nome
                    </button>
                  )}

                  {!justLinked && (
                    <>
                      <input ref={pdfFileRef} type="file" accept=".pdf" className="hidden" onChange={handleImportPdf} />
                      <button
                        disabled={importingPdf}
                        onClick={() => pdfFileRef.current?.click()}
                        className="w-full py-4 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-2xl font-black uppercase tracking-widest text-[10px] flex items-center justify-center gap-2 disabled:opacity-50"
                      >
                        {importingPdf ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                        Importar Cartão CNPJ
                      </button>
                    </>
                  )}
               </div>
               
               {!isSearchingCliente && !justLinked && (
                 <button onClick={() => setShowClienteSearch(false)} className="w-full py-2 text-slate-400 font-bold text-[10px] uppercase tracking-widest">Cancelar</button>
               )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* NOVO MODAL: BUSCA POR NOME COM AUTO-COMPLETE */}
      <AnimatePresence>
        {showNomeSearch && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => !isSearchingCliente && setShowNomeSearch(false)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="relative bg-white dark:bg-slate-800 w-full max-w-md rounded-[2.5rem] shadow-2xl p-8 space-y-6 flex flex-col max-h-[80vh]">
               <div className="text-center">
                 <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 transition-colors duration-500 ${justLinked ? 'bg-emerald-500 text-white' : 'bg-brand-50 text-brand-600'}`}>
                   {justLinked ? <Check className="w-8 h-8" /> : <Search className="w-8 h-8" />}
                 </div>
                 <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
                   {justLinked ? 'Cliente Vinculado!' : 'Buscar Cliente'}
                 </h3>
               </div>

               <div className="relative">
                 <input 
                  type="text" 
                  autoFocus
                  disabled={isSearchingCliente || justLinked}
                  placeholder="Digite o nome..." 
                  className="w-full px-6 py-5 bg-slate-50 dark:bg-slate-900 dark:text-white rounded-2xl outline-none font-black text-lg placeholder:text-slate-300 transition-all focus:ring-4 focus:ring-brand-500/10" 
                  value={nomeQuery} 
                  onChange={e => setNomeQuery(e.target.value)} 
                 />
               </div>

               <div className="flex-1 overflow-y-auto space-y-2 min-h-[200px] pr-2 custom-scrollbar">
                 {sugestoes.length > 0 ? (
                   sugestoes.map((s: any) => (
                     <button
                      key={s.id}
                      disabled={isSearchingCliente || justLinked}
                      onClick={() => handleVincularCliente(s.id, s)}
                      className="w-full p-4 bg-slate-50 dark:bg-slate-900 hover:bg-brand-50 dark:hover:bg-brand-900/20 rounded-2xl text-left transition-colors border border-transparent hover:border-brand-200 group"
                     >
                       <p className="font-black text-slate-900 dark:text-white group-hover:text-brand-600 transition-colors">{s.nome}</p>
                       <p className="text-[10px] text-slate-400 font-bold uppercase">{s.documento}</p>
                     </button>
                   ))
                 ) : nomeQuery.length >= 2 ? (
                   <div className="h-full flex flex-col items-center justify-center text-slate-400 py-10">
                     <User className="w-10 h-10 mb-2 opacity-20" />
                     <p className="font-bold text-xs uppercase tracking-widest">Nenhum cliente encontrado</p>
                   </div>
                 ) : (
                   <div className="h-full flex flex-col items-center justify-center text-slate-400 py-10">
                     <Search className="w-10 h-10 mb-2 opacity-20" />
                     <p className="font-bold text-xs uppercase tracking-widest">Digite pelo menos 2 letras</p>
                   </div>
                 )}
               </div>

               {!isSearchingCliente && !justLinked && (
                 <div className="grid grid-cols-2 gap-3">
                   <button 
                    onClick={() => { setShowNomeSearch(false); setShowClienteSearch(true); }}
                    className="py-4 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-2xl font-black uppercase tracking-widest text-[10px]"
                   >
                     CPF/CNPJ
                   </button>
                   <button onClick={() => setShowNomeSearch(false)} className="py-4 text-slate-400 font-bold text-[10px] uppercase tracking-widest">Fechar</button>
                 </div>
               )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
