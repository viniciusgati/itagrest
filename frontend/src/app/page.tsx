'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'

export default function RootPage() {
  const router = useRouter()

  useEffect(() => {
    const checkStatus = async () => {
      try {
        // 1. Verificar se o sistema precisa de setup inicial
        const resSetup = await api.get('/setup/status')
        
        if (resSetup.data.setup_needed) {
          router.push('/setup-admin')
          return
        }

        // 2. Se não precisa de setup, vai para o dashboard (ou login)
        // Nota: Em uma versão final, checaríamos o token JWT aqui.
        router.push('/dashboard')
      } catch (err) {
        console.error("Erro ao verificar status do sistema", err)
        // Fallback para login se a API falhar
        router.push('/login')
      }
    }

    checkStatus()
  }, [router])

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="animate-pulse flex flex-col items-center gap-4">
        <div className="w-12 h-12 bg-indigo-600 rounded-2xl rotate-45" />
        <p className="text-slate-400 font-black uppercase tracking-widest text-[10px]">Iniciando iTagREST...</p>
      </div>
    </div>
  )
}
