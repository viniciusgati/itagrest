'use client'

import { useState, useEffect } from 'react'
import { UserCog, Plus, Pencil, Trash2, Loader2, Check, X, Search, ShieldCheck, User } from 'lucide-react'
import api from '@/lib/api'

interface Usuario {
  id: number
  full_name: string
  username: string
  email: string
  papel: string
  is_active: number
  created_at: string
}

interface UsuarioForm {
  full_name: string
  username: string
  email: string
  password: string
  papel: string
}

const defaultForm: UsuarioForm = {
  full_name: '',
  username: '',
  email: '',
  password: '',
  papel: 'GARCOM',
}

export default function AdminUsuarios() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<UsuarioForm>(defaultForm)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const fetchUsers = async () => {
    try {
      const res = await api.get('/auth/users')
      setUsuarios(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchUsers() }, [])

  const openCreate = () => {
    setEditingId(null)
    setForm(defaultForm)
    setError('')
    setShowModal(true)
  }

  const openEdit = (u: Usuario) => {
    setEditingId(u.id)
    setForm({ full_name: u.full_name, username: u.username, email: u.email, password: '', papel: u.papel })
    setError('')
    setShowModal(true)
  }

  const handleSave = async () => {
    setSaving(true)
    setError('')
    try {
      if (editingId) {
        const payload: any = { full_name: form.full_name, email: form.email, papel: form.papel }
        if (form.password) payload.password = form.password
        await api.put(`/auth/users/${editingId}`, payload)
      } else {
        await api.post('/auth/register', form)
      }
      setShowModal(false)
      fetchUsers()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  const toggleActive = async (u: Usuario) => {
    try {
      await api.put(`/auth/users/${u.id}`, { is_active: u.is_active ? 0 : 1 })
      fetchUsers()
    } catch (err) {
      console.error(err)
    }
  }

  const filtered = usuarios.filter(u =>
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-6 md:p-10 flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-6 md:p-10 transition-colors">
      <div className="max-w-5xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
              <UserCog className="w-8 h-8 text-brand-500" />
              Usuários
            </h1>
            <p className="text-slate-500 dark:text-slate-400 font-medium">Gerencie os usuários do sistema</p>
          </div>
          <button
            onClick={openCreate}
            className="bg-slate-900 dark:bg-brand-600 hover:bg-slate-800 dark:hover:bg-brand-700 text-white font-bold py-3 px-6 rounded-2xl transition-all shadow-lg flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Novo Usuário
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por nome, usuário ou email..."
            className="w-full pl-12 pr-4 py-3.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 dark:focus:ring-brand-900/30 focus:border-brand-300 transition-all text-slate-900 dark:text-white placeholder-slate-400"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-400 p-4 rounded-2xl text-sm font-medium border border-rose-100 dark:border-rose-800">
            {error}
          </div>
        )}

        {/* Table */}
        <div className="bg-white dark:bg-slate-800 rounded-[2.5rem] shadow-xl border border-slate-100 dark:border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-700">
                  <th className="text-left py-4 px-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Nome</th>
                  <th className="text-left py-4 px-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Usuário</th>
                  <th className="text-left py-4 px-6 text-[10px] font-black text-slate-400 uppercase tracking-widest hidden md:table-cell">Email</th>
                  <th className="text-left py-4 px-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Função</th>
                  <th className="text-left py-4 px-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Status</th>
                  <th className="text-right py-4 px-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Ações</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(u => (
                  <tr key={u.id} className="border-b border-slate-50 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-700/20 transition-colors">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-brand-100 dark:bg-brand-900/30 rounded-xl flex items-center justify-center text-brand-600 font-black text-sm">
                          {u.full_name.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-bold text-slate-900 dark:text-white text-sm">{u.full_name}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-600 dark:text-slate-400 font-medium">{u.username}</td>
                    <td className="py-4 px-6 text-sm text-slate-500 dark:text-slate-500 hidden md:table-cell">{u.email}</td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-widest ${
                        u.papel === 'GERENTE'
                          ? 'bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400'
                          : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                      }`}>
                        {u.papel === 'GERENTE' ? <ShieldCheck className="w-3 h-3" /> : <User className="w-3 h-3" />}
                        {u.papel}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-widest ${
                        u.is_active
                          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                          : 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400'
                      }`}>
                        {u.is_active ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
                        {u.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openEdit(u)}
                          className="w-9 h-9 bg-slate-100 dark:bg-slate-700 rounded-xl flex items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-brand-50 hover:text-brand-600 transition-colors"
                          title="Editar"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => toggleActive(u)}
                          className={`w-9 h-9 rounded-xl flex items-center justify-center transition-colors ${
                            u.is_active
                              ? 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 hover:bg-rose-50 hover:text-rose-500'
                              : 'bg-emerald-100 text-emerald-600 hover:bg-emerald-200'
                          }`}
                          title={u.is_active ? 'Desativar' : 'Ativar'}
                        >
                          {u.is_active ? <Trash2 className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-16 text-center">
                      <UserCog className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
                      <p className="text-slate-400 dark:text-slate-500 font-bold">Nenhum usuário encontrado</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 rounded-[2.5rem] p-8 max-w-lg w-full shadow-2xl border border-slate-100 dark:border-slate-700 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-black text-slate-900 dark:text-white">
                {editingId ? 'Editar Usuário' : 'Novo Usuário'}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-600 dark:text-slate-400 ml-1">Nome Completo</label>
                <input
                  type="text"
                  className="w-full px-4 py-3.5 mt-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 dark:text-white"
                  value={form.full_name}
                  onChange={e => setForm({...form, full_name: e.target.value})}
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-600 dark:text-slate-400 ml-1">Usuário</label>
                <input
                  type="text"
                  className="w-full px-4 py-3.5 mt-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 dark:text-white"
                  value={form.username}
                  onChange={e => setForm({...form, username: e.target.value})}
                  disabled={!!editingId}
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-600 dark:text-slate-400 ml-1">Email</label>
                <input
                  type="email"
                  className="w-full px-4 py-3.5 mt-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 dark:text-white"
                  value={form.email}
                  onChange={e => setForm({...form, email: e.target.value})}
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-600 dark:text-slate-400 ml-1">
                  {editingId ? 'Nova Senha (deixe em branco para manter)' : 'Senha'}
                </label>
                <input
                  type="password"
                  className="w-full px-4 py-3.5 mt-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 dark:text-white"
                  value={form.password}
                  onChange={e => setForm({...form, password: e.target.value})}
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-600 dark:text-slate-400 ml-1">Função</label>
                <select
                  className="w-full px-4 py-3.5 mt-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 dark:text-white"
                  value={form.papel}
                  onChange={e => setForm({...form, papel: e.target.value})}
                >
                  <option value="GARCOM">Garçom</option>
                  <option value="GERENTE">Gerente</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-400 p-4 rounded-2xl text-sm font-medium border border-rose-100 dark:border-rose-800">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-4 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-600 dark:text-slate-300 font-bold rounded-2xl transition-all text-sm"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 py-4 bg-slate-900 dark:bg-brand-600 hover:bg-slate-800 dark:hover:bg-brand-700 disabled:bg-slate-400 text-white font-bold rounded-2xl transition-all shadow-lg flex items-center justify-center gap-2 text-sm"
              >
                {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : (editingId ? 'Salvar' : 'Criar')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
