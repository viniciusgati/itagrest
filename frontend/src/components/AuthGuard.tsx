'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { Loader2, TrendingUp } from 'lucide-react'

// Lista de rotas públicas que NÃO precisam de autenticação
const PUBLIC_ROUTES = ['/login', '/setup-admin']

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [authorized, setAuthorized] = useState(false)

  useEffect(() => {
    // 1. Verifica se a rota é pública
    if (PUBLIC_ROUTES.includes(pathname)) {
      setAuthorized(true)
      return
    }

    // 2. Verifica se existe o token no localStorage
    const token = localStorage.getItem('token')
    
    if (!token) {
      setAuthorized(false)
      router.push('/login')
    } else {
      setAuthorized(true)
    }
  }, [pathname, router])

  if (!authorized && !PUBLIC_ROUTES.includes(pathname)) {
    return (
      <div className="min-h-screen bg-slate-100 dark:bg-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <TrendingUp className="w-12 h-12 text-brand-600 animate-bounce" />
          <p className="font-black text-slate-400 uppercase tracking-widest text-[10px]">Protegendo sua conta...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
