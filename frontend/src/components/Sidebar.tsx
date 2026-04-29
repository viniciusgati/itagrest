'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard, UtensilsCrossed, Package, Users,
  ShieldCheck, UserCog, FileText, Settings,
  LogOut, Menu, X, ChevronDown, TrendingUp
} from 'lucide-react'
import api from '@/lib/api'

interface UserInfo {
  id: number
  full_name: string
  username: string
  email: string
  papel: string
  is_active: number
}

const principalLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/pdv', label: 'Terminal PDV', icon: UtensilsCrossed },
  { href: '/cardapio', label: 'Cardápio', icon: Package },
  { href: '/clientes', label: 'Clientes', icon: Users },
  { href: '/vendas', label: 'Vendas', icon: ShieldCheck },
]

const adminLinks = [
  { href: '/admin/usuarios', label: 'Usuários', icon: UserCog },
  { href: '/notas', label: 'Notas Fiscais', icon: FileText },
  { href: '/wizard-fiscal', label: 'Config. Fiscal', icon: Settings },
]

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [user, setUser] = useState<UserInfo | null>(null)
  const [adminExpanded, setAdminExpanded] = useState(false)

  const isPublicRoute = pathname === '/login' || pathname === '/setup-admin'

  useEffect(() => {
    if (!isPublicRoute) {
      api.get('/auth/me').then(res => setUser(res.data)).catch(() => {})
    }
  }, [pathname, isPublicRoute])

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/login')
  }

  if (isPublicRoute) return null

  const isGerente = user?.papel === 'GERENTE'
  const isActive = (href: string) => pathname === href || pathname.startsWith(href + '/')

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-40 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Mobile toggle */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed top-4 left-4 z-50 md:hidden w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-300"
      >
        {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-40 h-full w-72 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transition-transform duration-300 flex flex-col
          ${open ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0 md:static md:z-0`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-slate-100 dark:border-slate-700">
          <Link href="/dashboard" className="flex items-center gap-3" onClick={() => setOpen(false)}>
            <div className="w-10 h-10 bg-brand-500 rounded-2xl flex items-center justify-center text-white font-black text-lg">
              iT
            </div>
            <div>
              <h2 className="font-black text-slate-900 dark:text-white text-lg leading-tight">iTagREST</h2>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Gestão Inteligente</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Principal */}
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest px-3 mb-2">Principal</p>
            <div className="space-y-1">
              {principalLinks.map(link => (
                <SidebarLink
                  key={link.href}
                  href={link.href}
                  label={link.label}
                  icon={link.icon}
                  active={isActive(link.href)}
                  onNavigate={() => setOpen(false)}
                />
              ))}
            </div>
          </div>

          {/* Administrativo (GERENTE only) */}
          {isGerente && (
            <div>
              <button
                onClick={() => setAdminExpanded(!adminExpanded)}
                className="flex items-center justify-between w-full px-3 mb-2"
              >
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Administrativo</p>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${adminExpanded ? 'rotate-180' : ''}`} />
              </button>
              {(adminExpanded || open) && (
                <div className="space-y-1">
                  {adminLinks.map(link => (
                    <SidebarLink
                      key={link.href}
                      href={link.href}
                      label={link.label}
                      icon={link.icon}
                      active={isActive(link.href)}
                      onNavigate={() => setOpen(false)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </nav>

        {/* User info + Logout */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-700">
          {user && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 bg-brand-100 dark:bg-brand-900/30 rounded-2xl flex items-center justify-center text-brand-600 font-black text-sm shrink-0">
                  {user.full_name.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="font-bold text-sm text-slate-900 dark:text-white truncate">{user.full_name}</p>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{user.papel}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="w-9 h-9 bg-slate-100 dark:bg-slate-700 rounded-xl flex items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-rose-50 hover:text-rose-500 transition-colors shrink-0"
                title="Sair"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </aside>

    </>
  )
}

function SidebarLink({ href, label, icon: Icon, active, onNavigate }: {
  href: string
  label: string
  icon: any
  active: boolean
  onNavigate: () => void
}) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={`flex items-center gap-3 px-3 py-2.5 rounded-2xl transition-all text-sm font-bold ${
        active
          ? 'bg-brand-500 text-white shadow-lg shadow-brand-200 dark:shadow-none'
          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-white'
      }`}
    >
      <Icon className="w-5 h-5 shrink-0" />
      <span>{label}</span>
    </Link>
  )
}
