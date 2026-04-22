'use client'

import { useState, useEffect } from 'react'
import { Plus, Search, User, Edit2, Trash2, X, ArrowLeft, Loader2, Mail, Phone, FileText } from 'lucide-react'
import api from '@/lib/api'
import Link from 'next/link'
import { motion } from 'framer-motion'



export default function ClientesPage() {
  const [clientes, setClientes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCliente, setEditingCliente] = useState<any>(null)
  const [busca, setBusca] = useState('')

  const fetchClientes = async () => {
    setLoading(true)
    try {
      const res = await api.get('/clientes')
      setClientes(res.data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    fetchClientes()
  }, [])

  const openModal = (cliente: any = null) => {
    setEditingCliente(cliente)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setEditingCliente(null)
    setIsModalOpen(false)
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data = Object.fromEntries(formData.entries())

    try {
      if (editingCliente) {
        await api.put(`/clientes/${editingCliente.id}`, data)
      } else {
        await api.post('/clientes', data)
      }
      fetchClientes()
      closeModal()
    } catch (err: any) { 
      alert(err.response?.data?.detail || "Erro ao salvar cliente")
    }
  }

  const clientesFiltrados = clientes.filter(c => 
    c.nome.toLowerCase().includes(busca.toLowerCase()) || 
    c.documento.includes(busca)
  )

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-6 md:p-10 font-sans transition-colors duration-300">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10 text-slate-900 dark:text-white">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl flex items-center justify-center shadow-sm border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all">
              <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-300" />
            </Link>
            <div>
              <h1 className="text-4xl font-black tracking-tight">Clientes</h1>
              <p className="text-slate-500 dark:text-slate-400 mt-1">Gestão de clientes e faturamento nominal.</p>
            </div>
          </div>
          <button onClick={() => openModal()} className="px-8 py-4 bg-brand-600 hover:bg-brand-700 text-white rounded-2xl font-black text-sm uppercase tracking-widest transition-all shadow-lg flex items-center gap-3">
            <Plus className="w-5 h-5" /> Novo Cliente
          </button>
        </div>

        {/* Busca */}
        <div className="mb-10 bg-white dark:bg-slate-800 p-4 rounded-3xl shadow-sm border border-slate-100 dark:border-slate-700">
          <div className="relative">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input 
              type="text" 
              placeholder="Buscar por nome ou CPF/CNPJ..." 
              className="w-full pl-14 pr-6 py-4 bg-slate-50 dark:bg-slate-900 dark:text-white border-none rounded-2xl focus:ring-4 focus:ring-brand-100 dark:focus:ring-brand-900/30 outline-none font-bold transition-all" 
              value={busca} 
              onChange={e => setBusca(e.target.value)} 
            />
          </div>
        </div>

        {/* Listagem */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            [1,2,3].map(i => <div key={i} className="bg-white dark:bg-slate-800 h-48 rounded-[2.5rem] animate-pulse border border-slate-100 dark:border-slate-700" />)
          ) : clientesFiltrados.map((c) => (
            <div key={c.id} className="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] border border-slate-100 dark:border-slate-700 shadow-xl group hover:border-brand-300 transition-all text-slate-900 dark:text-white relative">
              <div className="absolute top-6 right-6 flex gap-2 opacity-0 group-hover:opacity-100 transition-all">
                <button onClick={() => openModal(c)} className="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg text-slate-400 hover:text-brand-600"><Edit2 className="w-4 h-4" /></button>
              </div>
              
              <div className="flex items-start gap-5">
                <div className="w-14 h-14 bg-slate-100 dark:bg-slate-900 rounded-2xl flex items-center justify-center text-slate-400">
                  <User className="w-8 h-8" />
                </div>
                <div className="flex-1">
                  <h3 className="font-black text-xl leading-tight">{c.nome}</h3>
                  <p className="text-brand-600 font-bold text-xs uppercase tracking-widest mt-1">{c.documento}</p>
                </div>
              </div>

              <div className="mt-8 grid grid-cols-2 gap-4 border-t border-slate-50 dark:border-slate-700 pt-6">
                <div className="flex items-center gap-2 text-slate-400">
                  <Mail className="w-4 h-4" />
                  <span className="text-xs font-medium truncate">{c.email || '-'}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <Phone className="w-4 h-4" />
                  <span className="text-xs font-medium">{c.telefone || '-'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal CRUD */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-md" onClick={closeModal} />
          <div className="relative bg-white dark:bg-slate-800 w-full max-w-2xl rounded-[3rem] shadow-2xl overflow-hidden flex flex-col max-h-[95vh] text-slate-900 dark:text-white">
            <div className="p-8 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
              <h2 className="text-2xl font-black uppercase tracking-tight">{editingCliente ? 'Editar Cliente' : 'Novo Cliente'}</h2>
              <button onClick={closeModal} className="p-3 text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-full"><X /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-8 space-y-6 overflow-y-auto">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Nome / Razão Social</label>
                  <input name="nome" defaultValue={editingCliente?.nome} required className="w-full px-6 py-4 bg-slate-50 dark:bg-slate-900 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 font-bold" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">CPF / CNPJ (Apenas números)</label>
                  <input name="documento" defaultValue={editingCliente?.documento} required className="w-full px-6 py-4 bg-slate-50 dark:bg-slate-900 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 font-bold" />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">E-mail</label>
                  <input name="email" type="email" defaultValue={editingCliente?.email} className="w-full px-6 py-4 bg-slate-50 dark:bg-slate-900 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 font-bold" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Telefone</label>
                  <input name="telefone" defaultValue={editingCliente?.telefone} className="w-full px-6 py-4 bg-slate-50 dark:bg-slate-900 border-none rounded-2xl focus:ring-2 focus:ring-brand-500 font-bold" />
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-700">
                <h4 className="text-xs font-black uppercase text-slate-400 tracking-widest">Endereço (Opcional)</h4>
                <div className="grid grid-cols-4 gap-4">
                  <div className="col-span-3 space-y-1">
                    <input name="logradouro" placeholder="Logradouro" defaultValue={editingCliente?.logradouro} className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 rounded-xl" />
                  </div>
                  <div className="space-y-1">
                    <input name="numero" placeholder="Nº" defaultValue={editingCliente?.numero} className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 rounded-xl" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-1">
                    <input name="bairro" placeholder="Bairro" defaultValue={editingCliente?.bairro} className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 rounded-xl" />
                  </div>
                  <div className="space-y-1">
                    <input name="municipio_nome" placeholder="Cidade" defaultValue={editingCliente?.municipio_nome} className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 rounded-xl" />
                  </div>
                  <div className="space-y-1">
                    <input name="uf" placeholder="UF" maxLength={2} defaultValue={editingCliente?.uf} className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-900 rounded-xl uppercase" />
                  </div>
                </div>
              </div>

              <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-2xl border border-amber-100 dark:border-amber-800 text-[10px] text-amber-700 dark:text-amber-400 font-bold uppercase tracking-widest leading-relaxed">
                Atenção: Para emissão fiscal real, garanta que o CPF/CNPJ e a UF estejam corretos.
              </div>

              <div className="pt-6 flex justify-end gap-4">
                <button type="button" onClick={closeModal} className="px-8 py-4 font-black uppercase text-xs text-slate-400 tracking-widest">Cancelar</button>
                <button type="submit" className="px-10 py-4 bg-brand-600 text-white font-black rounded-2xl shadow-xl shadow-brand-100 dark:shadow-none hover:bg-brand-700 transition-all uppercase text-xs tracking-widest">Salvar Cliente</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
