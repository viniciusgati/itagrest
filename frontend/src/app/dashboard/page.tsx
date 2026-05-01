'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Users, DollarSign, Package, ArrowUpRight, ArrowDownRight, ShieldCheck, UtensilsCrossed, Sun, Moon, Loader2, Eye, EyeOff } from 'lucide-react'
import api from '@/lib/api'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts'
import Link from 'next/link'
import { useTheme } from '../theme-provider'

export default function DashboardPage() {
  const { isDark, toggleTheme } = useTheme()
  const [resumo, setResumo] = useState<any>(null)
  const [faturamento, setFaturamento] = useState<any[]>([])
  const [topProdutos, setTopProdutos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [empresaConfigurada, setEmpresaConfigurada] = useState(true)
  const [dias, setDias] = useState(7)
  const [papel, setPapel] = useState<string | null>(null)

  const isGerente = papel === 'GERENTE'

  const fetchData = async (periodo: number) => {
    setIsRefreshing(true)
    try {
      const resStatus = await api.get('/empresa/status')
      setEmpresaConfigurada(resStatus.data.configurado)

      const resMe = await api.get('/auth/me')
      setPapel(resMe.data.papel)

      const [resResumo, resFat, resTop] = await Promise.all([
        api.get(`/vendas/stats/resumo?dias=${periodo}`),
        api.get(`/vendas/stats/faturamento-periodo?dias=${periodo}`),
        api.get(`/vendas/stats/top-produtos?dias=${periodo}`)
      ])
      setResumo(resResumo.data)
      setFaturamento(resFat.data)
      setTopProdutos(resTop.data)
    } catch (err) { console.error(err) }
    finally { 
      setLoading(false) 
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData(dias)
  }, [dias])

  const formatPeriodo = (val: string) => {
    if (dias > 30) {
      const [year, month] = val.split('-')
      return `${month}/${year.slice(2)}`
    }
    const parts = val.split('-')
    return `${parts[2]}/${parts[1]}`
  }

  const maskVal = (val: any) => isGerente ? val : '***'
  const maskMoney = (val: any) => isGerente ? `R$ ${Number(val || 0).toFixed(2)}` : 'R$ ***'

  const formatTrend = (val: number | null | undefined) => {
    if (val == null) return null
    return `${val >= 0 ? '+' : ''}${val.toFixed(1)}%`
  }

  if (loading) return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 p-10 flex items-center justify-center transition-colors">
      <div className="flex flex-col items-center gap-4">
        <TrendingUp className="w-12 h-12 text-brand-600 animate-bounce" />
        <p className="font-black text-slate-400 uppercase tracking-widest text-[10px]">Carregando Inteligência...</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 transition-colors duration-300 p-6 md:p-10 flex flex-col gap-10">
      
      {!empresaConfigurada && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-900/40 backdrop-blur-md animate-in fade-in duration-500">
          <div className="bg-white dark:bg-slate-800 rounded-[3rem] p-10 max-w-lg w-full shadow-2xl border border-slate-100 dark:border-slate-700 text-center space-y-8 animate-in zoom-in-95 duration-500">
            <div className="w-20 h-20 bg-brand-50 dark:bg-brand-900/20 rounded-3xl flex items-center justify-center mx-auto text-brand-600">
              <ShieldCheck className="w-10 h-10" />
            </div>
            <div className="space-y-2">
              <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">Ative seu iTagREST</h2>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed font-medium">
                Seu setup administrativo está pronto! Agora precisamos configurar seus dados fiscais e o certificado para emitir NFC-e.
              </p>
            </div>
            <div className="flex flex-col gap-4">
              <button 
                onClick={() => window.location.href = '/wizard-fiscal'}
                className="w-full bg-slate-900 dark:bg-brand-600 hover:bg-slate-800 dark:hover:bg-brand-700 text-white font-black py-5 rounded-2xl transition-all shadow-xl shadow-slate-200 dark:shadow-none flex items-center justify-center gap-3"
              >
                Configurar Empresa e Fiscal <ArrowUpRight className="w-5 h-5" />
              </button>
              <button 
                onClick={() => setEmpresaConfigurada(true)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 text-xs font-bold uppercase tracking-widest transition-colors"
              >
                Pular por agora (Apenas Visualização)
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto w-full space-y-10">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight">Painel de Controle</h1>
            <p className="text-slate-500 dark:text-slate-400 font-medium">Bem-vindo ao iTagREST Intelligence.</p>
          </div>
          
          <div className="flex items-center gap-4">
            {!isGerente && (
              <div className="flex items-center gap-2 px-4 py-2 bg-amber-50 dark:bg-amber-900/20 rounded-2xl text-[10px] font-black text-amber-600 dark:text-amber-400 uppercase tracking-widest">
                <EyeOff className="w-3 h-3" /> Valores ocultos
              </div>
            )}
            {isRefreshing && <Loader2 className="w-5 h-5 text-brand-500 animate-spin" />}
            
            <button 
              onClick={toggleTheme}
              className="w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-300 hover:bg-slate-50 transition-all active:scale-95"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            <div className="bg-white dark:bg-slate-800 p-1.5 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 flex items-center gap-1">
              {[7, 15, 30, 365].map((d) => (
                <button
                  key={d}
                  onClick={() => setDias(d)}
                  className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                    dias === d 
                      ? 'bg-slate-900 dark:bg-brand-600 text-white shadow-lg' 
                      : 'text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700'
                  }`}
                >
                  {d === 365 ? '1 Ano' : `${d}D`}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Ações Rápidas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <QuickAction 
            href="/cardapio" 
            title="Cardápio" 
            desc="Produtos e Preços" 
            icon={<Package className="w-5 h-5" />} 
            color="bg-brand-600"
          />
          <QuickAction 
            href="/clientes" 
            title="Clientes" 
            desc="Cadastro Nominal" 
            icon={<Users className="w-5 h-5" />} 
            color="bg-violet-600"
          />
          <QuickAction 
            href="/pdv" 
            title="Terminal PDV" 
            desc="Vendas em Aberto" 
            icon={<UtensilsCrossed className="w-5 h-5" />} 
            color="bg-emerald-600"
          />
          <QuickAction 
            href="/vendas" 
            title="Monitor" 
            desc="Histórico de Vendas" 
            icon={<ShieldCheck className="w-5 h-5" />} 
            color="bg-slate-900 dark:bg-slate-700"
          />
        </div>

        {/* Widgets de Resumo */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard 
            title={`Faturamento (${dias > 30 ? '1 Ano' : `${dias}D`})`} 
            value={maskMoney(resumo?.total_faturado)} 
            trend={formatTrend(resumo?.variacao_faturamento)}
            icon={<DollarSign className="w-6 h-6" />}
            color="bg-emerald-500"
          />
          <StatCard 
            title="Vendas Realizadas" 
            value={maskVal(resumo?.qtd_vendas)} 
            trend={formatTrend(resumo?.variacao_qtd)}
            icon={<Users className="w-6 h-6" />}
            color="bg-brand-500"
          />
          <StatCard 
            title="Ticket Médio" 
            value={maskMoney(resumo?.ticket_medio)} 
            trend={formatTrend(resumo?.variacao_ticket)}
            icon={<TrendingUp className="w-6 h-6" />}
            color="bg-violet-500"
          />
        </div>

        {/* Gráfico de Faturamento */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 bg-white dark:bg-slate-800 p-10 rounded-[3rem] shadow-xl shadow-slate-200/40 dark:shadow-none border border-slate-100 dark:border-slate-700 flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight">Faturamento por {dias > 30 ? 'Mês' : 'Dia'}</h3>
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400">
                <span className="w-3 h-3 rounded-full bg-brand-500"></span> Total Processado
              </div>
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={faturamento}>
                  <defs>
                    <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6b8ef9" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#6b8ef9" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={isDark ? "#334155" : "#f1f5f9"} />
                  <XAxis 
                    dataKey="periodo" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{fill: '#94a3b8', fontSize: 10, fontWeight: 700}} 
                    dy={10} 
                    tickFormatter={formatPeriodo}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{fill: '#94a3b8', fontSize: 10, fontWeight: 700}} 
                    tickFormatter={(v: number) => isGerente ? `R$${v}` : ''}
                  />
                  <Tooltip 
                    contentStyle={{ borderRadius: '20px', border: 'none', boxShadow: '0 20px 50px rgba(0,0,0,0.1)', padding: '15px' }}
                    itemStyle={{ fontWeight: 800, color: '#1e293b' }}
                    labelFormatter={formatPeriodo}
                    formatter={(value: number) => isGerente ? [`R$ ${value.toFixed(2)}`, 'Total'] : ['R$ ***', 'Total']}
                  />
                  <Area type="monotone" dataKey="total" stroke="#6b8ef9" strokeWidth={4} fillOpacity={1} fill="url(#colorTotal)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Ranking de Produtos */}
          <div className="bg-white dark:bg-slate-800 p-10 rounded-[3rem] shadow-xl shadow-slate-200/40 dark:shadow-none border border-slate-100 dark:border-slate-700 flex flex-col gap-8 text-slate-900 dark:text-white">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-black uppercase tracking-tight">Mais Vendidos</h3>
              <Package className="text-brand-500 w-6 h-6" />
            </div>
            <div className="space-y-6">
              {topProdutos.map((p: any, i: number) => (
                <div key={i} className="flex items-center justify-between group">
                  <div className="flex items-center gap-4">
                    <span className="text-2xl font-black text-slate-200 dark:text-slate-700 group-hover:text-brand-500 transition-colors">0{i+1}</span>
                    <div>
                      <p className="font-bold text-sm leading-tight">{p.produto}</p>
                      <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">{isGerente ? `${p.qtd} unidades` : '** un'}</p>
                    </div>
                  </div>
                  <div className="h-1.5 w-16 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full bg-brand-500" style={{ width: `${(p.qtd / (topProdutos[0]?.qtd || 1)) * 100}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color, trend }: any) {
  return (
    <div className="bg-white dark:bg-slate-800 p-8 rounded-[2.5rem] shadow-xl shadow-slate-200/40 dark:shadow-none border border-slate-100 dark:border-slate-700 flex items-center justify-between group hover:border-brand-200 transition-all">
      <div className="space-y-2">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{title}</p>
        <h4 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">{value}</h4>
        {trend != null && (
          <div className={`flex items-center gap-1 text-[10px] font-black uppercase ${
            trend.startsWith('+') ? 'text-emerald-500' : trend.startsWith('-') ? 'text-rose-500' : 'text-slate-400'
          }`}>
            {trend.startsWith('+') ? <ArrowUpRight className="w-3 h-3" /> : trend.startsWith('-') ? <ArrowDownRight className="w-3 h-3" /> : null}
            {trend} este mês
          </div>
        )}
      </div>
      <div className={`w-16 h-16 ${color} rounded-3xl flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
    </div>
  )
}

function QuickAction({ href, title, desc, icon, color }: any) {
  return (
    <Link href={href} className="group bg-white dark:bg-slate-800 p-6 rounded-[2rem] border border-slate-100 dark:border-slate-700 shadow-xl shadow-slate-200/30 dark:shadow-none hover:border-brand-300 transition-all flex items-center gap-5">
      <div className={`w-14 h-14 ${color} rounded-2xl flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <div>
        <h4 className="font-black text-slate-900 dark:text-white leading-tight group-hover:text-brand-600 transition-colors">{title}</h4>
        <p className="text-slate-400 text-[10px] font-bold uppercase tracking-widest mt-0.5">{desc}</p>
      </div>
    </Link>
  )
}