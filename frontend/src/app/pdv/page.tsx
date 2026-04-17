'use client'

import { useState, useEffect, useRef } from 'react'
import { UtensilsCrossed, Search, ShoppingCart, X, ChevronRight, CreditCard, QrCode, DollarSign, Check, Loader2, ArrowLeft, Trash2, RotateCcw, FileText } from 'lucide-react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { QRCodeSVG } from 'qrcode.react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

const API_VENDAS = 'http://localhost:8000/api/v1/vendas'
const API_PRODUTOS = 'http://localhost:8000/api/v1/produtos'
const API_NOTAS = 'http://localhost:8000/api/v1/notas'

export default function PDVPage() {
  const router = useRouter()
  const [mesas, setMesas] = useState<any[]>([])
  const [produtos, setProdutos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectingMesa, setSelectingMesa] = useState<number | null>(null)

  const fetchMesas = async () => {
    try {
      const res = await axios.get(`${API_VENDAS}/mesas`)
      setMesas(res.data)
    } catch (err) { console.error(err) }
  }

  const fetchProdutos = async () => {
    try {
      const res = await axios.get(API_PRODUTOS)
      setProdutos(res.data)
    } catch (err) { console.error(err) }
  }

  useEffect(() => {
    fetchMesas()
    fetchProdutos()
    setLoading(false)
  }, [])

  const handleSelectMesa = (mesa: any) => {
    setSelectingMesa(mesa.mesa)
    router.push(`/pdv/comanda/${mesa.mesa}`)
  }

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-white p-6 md:p-10 flex flex-col gap-8 font-sans transition-colors duration-300">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-700 transition-all border border-slate-200 dark:border-slate-700 shadow-lg shadow-black/5">
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </Link>
          <div>
            <h1 className="text-3xl font-black tracking-tight">Mapa de Mesas</h1>
            <p className="text-slate-400 font-medium uppercase text-[10px] tracking-widest italic">Terminal de Operação em Tempo Real</p>
          </div>
        </div>
        <Link href="/vendas" className="flex items-center gap-2 px-6 py-3 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl text-xs font-black uppercase tracking-widest border border-slate-200 dark:border-slate-700 transition-all shadow-lg shadow-black/5">
          <FileText className="w-4 h-4 text-brand-500" /> Monitor
        </Link>
      </div>

      {/* Grid de Mesas */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-6">
        {mesas.map((m) => (
          <motion.button
            key={m.mesa}
            disabled={selectingMesa !== null}
            whileHover={selectingMesa === null ? { scale: 1.05 } : {}}
            whileTap={selectingMesa === null ? { scale: 0.95 } : {}}
            onClick={() => handleSelectMesa(m)}
            className={`h-40 rounded-[2.5rem] border-4 flex flex-col items-center justify-center gap-2 transition-all shadow-xl relative ${
              selectingMesa === m.mesa ? 'opacity-50 ring-4 ring-brand-500 ring-offset-4 dark:ring-offset-slate-900' : ''
            } ${
              m.status === 'LIVRE' 
                ? 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-400 hover:border-brand-500' 
                : m.status === 'EM_ATENDIMENTO'
                ? 'bg-brand-600 border-brand-500 text-white shadow-brand-900/20'
                : 'bg-amber-500 border-amber-400 text-white shadow-amber-900/20'
            }`}
          >
            {selectingMesa === m.mesa && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/5 rounded-[2.5rem]">
                <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
              </div>
            )}
            <span className="text-[10px] font-black uppercase tracking-tighter opacity-60">Mesa</span>
            <span className="text-5xl font-black leading-none">{m.mesa}</span>
            {m.total > 0 && <span className="text-sm font-bold bg-black/20 px-3 py-1 rounded-full">R$ {m.total}</span>}
          </motion.button>
        ))}
      </div>
    </div>
  )
}
