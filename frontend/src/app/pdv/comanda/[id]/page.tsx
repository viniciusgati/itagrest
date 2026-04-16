'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { 
  ArrowLeft, Search, Plus, Trash2, 
  CreditCard, X, Check, Loader2, DollarSign, 
  QrCode, Utensils, ShoppingBag
} from 'lucide-react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { QRCodeSVG } from 'qrcode.react'

const API_VENDAS = 'http://localhost:8000/api/v1/vendas'
const API_PRODUTOS = 'http://localhost:8000/api/v1/produtos'
const API_NOTAS = 'http://localhost:8000/api/v1/notas'

export default function ComandaMobilePage() {
  const { id } = useParams()
  const router = useRouter()
  const [venda, setVenda] = useState<any>(null)
  const [produtos, setProdutos] = useState<any[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCheckout, setShowCheckout] = useState(false)
  const [showAddItems, setShowAddItems] = useState(false)
  const [isEmitting, setIsEmitting] = useState(false)
  const [fiscalStatus, setFiscalStatus] = useState<any>(null)
  const [error, setError] = useState('')

  const fetchVenda = async () => {
    try {
      const res = await axios.post(API_VENDAS, { mesa: parseInt(id as string) })
      setVenda(res.data)
    } catch (err) { console.error(err) }
  }

  const fetchProdutos = async () => {
    try {
      const res = await axios.get(API_PRODUTOS)
      setProdutos(res.data)
    } catch (err) { console.error(err) }
  }

  useEffect(() => {
    Promise.all([fetchVenda(), fetchProdutos()]).finally(() => setLoading(false))
  }, [id])

  const handleAddItem = async (produto: any) => {
    if (!venda?.id) {
      alert("Comanda não carregada corretamente.")
      return
    }
    try {
      const res = await axios.post(`${API_VENDAS}/${venda.id}/itens`, {
        produto_id: produto.id,
        quantidade: 1
      })
      setVenda(res.data)
      // Pequeno feedback de vibração/sucesso aqui se possível
    } catch (err: any) { 
      console.error(err)
      alert(err.response?.data?.detail || "Erro ao lançar item.")
    }
  }

  const handleRemoveItem = async (ids: number[]) => {
    const lastId = ids[ids.length - 1]
    try {
      const res = await axios.delete(`${API_VENDAS}/${venda.id}/itens/${lastId}`)
      setVenda(res.data)
    } catch (err) { console.error(err) }
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

  const handleFecharMesa = async (forma: string) => {
    setIsEmitting(forma === 'DINHEIRO')
    try {
      const res = await axios.put(`${API_VENDAS}/${venda.id}/fechar`, {
        forma_pagamento: forma,
        status: forma === 'PIX' ? 'AGUARDANDO_PAGAMENTO' : 'PAGA'
      })
      setVenda(res.data)
      if (forma === 'DINHEIRO') {
        const resNota = await axios.post(`${API_NOTAS}/emitir/${venda.id}`)
        setFiscalStatus(resNota.data)
        setTimeout(() => router.push('/pdv'), 3000)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erro no fechamento")
    } finally { setIsEmitting(false) }
  }

  if (loading) return <div className="min-h-screen bg-slate-100 dark:bg-slate-900 flex items-center justify-center"><Loader2 className="animate-spin w-8 h-8 text-brand-600" /></div>

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 flex flex-col font-sans transition-colors duration-300">
      
      {/* Top Bar Fixa */}
      <div className="sticky top-0 z-40 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-5 flex items-center justify-between shadow-sm">
        <button onClick={() => router.push('/pdv')} className="p-2 -ml-2 text-slate-400">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <div className="text-center">
          <h1 className="font-black text-slate-900 dark:text-white uppercase tracking-tighter text-xl">Mesa {id}</h1>
          <div className="flex items-center justify-center gap-1.5">
            <div className={`w-2 h-2 rounded-full animate-pulse ${venda?.status === 'ABERTA' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">{venda?.status}</p>
          </div>
        </div>
        <button onClick={() => window.location.reload()} className="p-2 text-slate-300">
            <Loader2 className="w-5 h-5" />
        </button>
      </div>

      {/* Área Principal: Consumo Consolidado */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8 pb-32">
        <div className="flex items-center justify-between">
            <h3 className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">Resumo do Consumo</h3>
            <span className="text-[10px] font-black text-brand-600 bg-brand-50 dark:bg-brand-900/20 px-3 py-1 rounded-full uppercase">ID #{venda?.id}</span>
        </div>

        <div className="space-y-3">
          {getItensAgrupados().map((item: any) => (
            <motion.div 
              layout
              key={item.produto_id} 
              className="bg-white dark:bg-slate-800 p-5 rounded-[2rem] flex items-center justify-between shadow-sm border border-slate-50 dark:border-slate-700/50 transition-all"
            >
              <div className="flex-1">
                <h4 className="font-black text-slate-900 dark:text-white leading-tight">{item.produto.descricao}</h4>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="px-2.5 py-1 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-[11px] font-black rounded-xl">{item.quantidade}x</span>
                  <span className="text-[11px] text-slate-400 font-bold uppercase tracking-tighter">R$ {parseFloat(item.preco_unitario).toFixed(2)}</span>
                </div>
              </div>
              <div className="flex items-center gap-5">
                <span className="font-black text-slate-900 dark:text-white text-lg">R$ {item.subtotal.toFixed(2)}</span>
                <button onClick={() => handleRemoveItem(item.ids_originais)} className="p-3 bg-rose-50 dark:bg-rose-900/20 text-rose-500 rounded-2xl active:scale-90 transition-all">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}

          {venda?.itens?.length === 0 && (
            <div className="py-24 text-center space-y-6">
              <div className="w-20 h-20 bg-slate-50 dark:bg-slate-800/50 rounded-[2.5rem] flex items-center justify-center mx-auto text-slate-200 dark:text-slate-700 shadow-inner">
                <ShoppingBag className="w-10 h-10" />
              </div>
              <p className="text-slate-400 font-bold uppercase tracking-[0.2em] text-xs">Mesa vazia. Comece a lançar!</p>
            </div>
          )}
        </div>
      </div>

      {/* Botão Flutuante (FAB) para Adicionar Itens */}
      <motion.button 
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowAddItems(true)}
        className="fixed bottom-32 right-6 w-16 h-16 bg-brand-600 text-white rounded-2xl shadow-2xl shadow-brand-500/40 flex items-center justify-center z-40 transition-transform active:rotate-90"
      >
        <Plus className="w-8 h-8" />
      </motion.button>

      {/* Footer Fixo: Total e Checkout */}
      <div className="fixed bottom-0 inset-x-0 bg-white dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 p-6 flex flex-col gap-4 shadow-[0_-20px_50px_rgba(0,0,0,0.08)] rounded-t-[3rem] z-30">
        <div className="flex items-center justify-between px-4">
          <span className="text-slate-400 dark:text-slate-500 font-black uppercase text-xs tracking-widest">Subtotal</span>
          <span className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">R$ {parseFloat(venda?.total || "0").toFixed(2)}</span>
        </div>
        <button 
          disabled={!venda?.itens?.length}
          onClick={() => setShowCheckout(true)}
          className="w-full bg-slate-900 dark:bg-brand-600 hover:bg-black text-white font-black py-5 rounded-[1.5rem] shadow-xl flex items-center justify-center gap-3 active:scale-[0.98] transition-all disabled:opacity-30"
        >
          <Check className="w-5 h-5" /> FECHAR CONTA
        </button>
      </div>

      {/* Modal/Drawer de Lançamento de Itens */}
      <AnimatePresence>
        {showAddItems && (
          <motion.div 
            initial={{ y: '100%' }} 
            animate={{ y: 0 }} 
            exit={{ y: '100%' }} 
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-0 z-50 bg-white dark:bg-slate-900 flex flex-col"
          >
            <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-slate-800">
              <h2 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tighter">Lançar Produtos</h2>
              <button onClick={() => setShowAddItems(false)} className="w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center text-slate-500 dark:text-slate-300">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6 flex-1 overflow-y-auto pb-10">
              <div className="relative">
                <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input 
                  type="text" 
                  placeholder="Pesquisar no cardápio..."
                  autoFocus
                  className="w-full pl-14 pr-6 py-5 bg-slate-50 dark:bg-slate-800 dark:text-white rounded-[1.5rem] border-none shadow-inner outline-none focus:ring-4 focus:ring-brand-100 dark:focus:ring-brand-900/30 font-bold transition-all"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {produtos.filter(p => p.descricao.toLowerCase().includes(search.toLowerCase())).map(p => (
                  <button key={p.id} onClick={() => handleAddItem(p)} className="bg-white dark:bg-slate-800 p-4 rounded-[2rem] shadow-sm border border-slate-100 dark:border-slate-700 text-left space-y-3 active:scale-95 transition-all group relative">
                    <div className="h-28 bg-slate-50 dark:bg-slate-700/50 rounded-2xl overflow-hidden relative">
                      {p.imagem_url ? <img src={`http://localhost:8000${p.imagem_url}`} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-slate-200 dark:text-slate-600"><Utensils className="w-8 h-8" /></div>}
                      <div className="absolute inset-0 bg-brand-600/0 group-active:bg-brand-600/20 transition-colors flex items-center justify-center">
                        <Plus className="text-white opacity-0 group-active:opacity-100 w-10 h-10" />
                      </div>
                    </div>
                    <div>
                      <h4 className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">{p.unidade}</h4>
                      <h4 className="text-xs font-black text-slate-900 dark:text-white truncate mt-0.5">{p.descricao}</h4>
                      <p className="text-brand-600 font-black text-base mt-1">R$ {parseFloat(p.preco_venda).toFixed(2)}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="p-6 bg-slate-50 dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
                <button 
                  onClick={() => setShowAddItems(false)}
                  className="w-full bg-slate-900 dark:bg-white dark:text-slate-900 text-white font-black py-5 rounded-[1.5rem] uppercase tracking-widest text-sm shadow-xl"
                >
                  Concluir Lançamentos
                </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Modal de Checkout */}
      <AnimatePresence>
        {showCheckout && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 bg-slate-900/95 backdrop-blur-2xl p-6 flex flex-col justify-center">
            <div className="bg-white dark:bg-slate-800 rounded-[3rem] p-10 space-y-8 shadow-2xl relative overflow-hidden">
              <button onClick={() => setShowCheckout(false)} className="absolute top-6 right-6 p-2 text-slate-300 hover:text-slate-500"><X /></button>
              
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight uppercase">Checkout</h2>
                <p className="text-slate-400 font-medium">Mesa {id} · Total Final R$ {parseFloat(venda?.total || "0").toFixed(2)}</p>
              </div>

              {isEmitting ? (
                <div className="py-10 text-center space-y-6">
                  <Loader2 className="w-16 h-16 text-brand-600 animate-spin mx-auto" />
                  <p className="font-black text-slate-900 dark:text-white uppercase tracking-widest text-xs">Comunicando com SEFAZ...</p>
                </div>
              ) : fiscalStatus ? (
                <div className="py-10 text-center space-y-6">
                  <div className="w-24 h-24 bg-emerald-100 dark:bg-emerald-900/20 rounded-full flex items-center justify-center text-emerald-600 mx-auto"><Check className="w-12 h-12" /></div>
                  <p className="text-2xl font-black text-emerald-600 uppercase">Nota Autorizada!</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  <button onClick={() => handleFecharMesa('DINHEIRO')} className="h-28 bg-emerald-600 hover:bg-emerald-700 text-white rounded-[2rem] flex items-center justify-center gap-6 font-black uppercase tracking-widest shadow-lg transition-all active:scale-95">
                    <DollarSign className="w-8 h-8" /> 
                    <div className="text-left">
                        <span className="block text-xl">Dinheiro</span>
                        <span className="block text-[10px] text-emerald-100 opacity-80">NFC-e Automática</span>
                    </div>
                  </button>
                  <button onClick={() => handleFecharMesa('PIX')} className="h-24 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-900 dark:text-white rounded-[2rem] flex items-center justify-center gap-4 font-black uppercase tracking-widest transition-all active:scale-95">
                    <QrCode className="w-6 h-6 text-brand-600" /> PIX
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
