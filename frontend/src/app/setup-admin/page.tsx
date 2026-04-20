'use client'

import { useState, useEffect } from 'react'
import { User, Mail, Lock, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'
import api from '@/lib/api'

export default function SetupAdmin() {
  const [formData, setFormData] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
    confirm_password: ''
  })
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [validationError, setValidationError] = useState('')
  const [success, setSuccess] = useState(false)

  // Debouncing para validação instantânea de senha
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.password && formData.confirm_password) {
        if (formData.password !== formData.confirm_password) {
          setValidationError('As senhas não coincidem.')
        } else if (formData.password.length < 8) {
          setValidationError('A senha deve ter pelo menos 8 caracteres.')
        } else {
          setValidationError('')
        }
      } else {
        setValidationError('')
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [formData.password, formData.confirm_password])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (validationError) return

    setLoading(true)
    setError('')

    try {
      await api.post('/setup/setup-admin', {
        full_name: formData.full_name,
        username: formData.username,
        email: formData.email,
        password: formData.password
      })
      
      setSuccess(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao configurar administrador.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <div className="bg-white p-12 rounded-3xl shadow-2xl text-center max-w-md w-full border border-slate-100 animate-in fade-in zoom-in duration-500">
          <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-10 h-10 text-emerald-600" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-4 tracking-tight">Tudo Pronto!</h1>
          <p className="text-slate-600 mb-8 leading-relaxed">
            Seu acesso administrativo foi configurado com sucesso. Agora você pode entrar e configurar seu restaurante.
          </p>
          <button 
            onClick={() => window.location.href = '/login'}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white font-semibold py-4 rounded-2xl transition-all shadow-lg hover:shadow-brand-200"
          >
            Acessar o Sistema
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 font-sans">
      <div className="bg-white p-10 rounded-3xl shadow-2xl max-w-lg w-full border border-slate-100">
        <div className="text-center mb-10">
          <div className="inline-block px-4 py-1.5 bg-brand-50 text-brand-600 text-sm font-bold rounded-full mb-4">
            PRIMEIRO ACESSO
          </div>
          <h1 className="text-3xl font-black text-slate-900 mb-2">Seja bem-vindo!</h1>
          <p className="text-slate-500">Defina suas credenciais de administrador para começar.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="bg-red-50 text-red-600 p-4 rounded-2xl text-sm font-medium border border-red-100 animate-pulse flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              {error}
            </div>
          )}

          {validationError && (
            <div className="bg-amber-50 text-amber-600 p-4 rounded-2xl text-sm font-medium border border-amber-100 flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
              <AlertCircle className="w-5 h-5" />
              {validationError}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-sm font-bold text-slate-700 ml-1">Nome Completo</label>
            <div className="relative group">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-brand-500 transition-colors" />
              <input 
                required
                type="text" 
                placeholder="Ex: João Silva"
                className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 placeholder:text-slate-400"
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700 ml-1">Usuário</label>
              <input 
                required
                type="text" 
                placeholder="admin"
                className="w-full px-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 placeholder:text-slate-400"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-bold text-slate-700 ml-1">E-mail</label>
              <div className="relative">
                <Mail className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input 
                  required
                  type="email" 
                  placeholder="admin@restaurante.com"
                  className="w-full pl-4 pr-12 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 placeholder:text-slate-400"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-bold text-slate-700 ml-1">Senha</label>
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-brand-500 transition-colors" />
              <input 
                required
                type="password" 
                placeholder="••••••••"
                className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 placeholder:text-slate-400"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-bold text-slate-700 ml-1">Confirme a Senha</label>
            <input 
              required
              type="password" 
              placeholder="••••••••"
              className="w-full px-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-brand-100 focus:border-brand-300 transition-all text-slate-900 placeholder:text-slate-400"
              value={formData.confirm_password}
              onChange={(e) => setFormData({...formData, confirm_password: e.target.value})}
            />
          </div>

          <button 
            disabled={loading}
            className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white font-bold py-5 rounded-2xl transition-all shadow-xl active:scale-[0.98] flex items-center justify-center gap-2 mt-4"
          >
            {loading ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              'Finalizar Configuração'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
