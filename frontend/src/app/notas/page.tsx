'use client'

import { useState, useEffect } from 'react'
import { FileText, CheckCircle2, AlertCircle, Search, ExternalLink, Download, RefreshCcw } from 'lucide-react'
import axios from 'axios'

const API_NOTAS = 'http://localhost:8000/api/v1/notas'

export default function MonitorFiscalPage() {
  const [notas, setNotas] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchNotas = async () => {
    setLoading(true)
    try {
      // Nota: Precisamos de um endpoint para listar todas as notas. 
      // Vou criar no backend logo após este passo.
      const res = await axios.get(`${API_NOTAS}/todas`)
      setNotas(res.data)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => {
    fetchNotas()
  }, [])

  return (
    <div className="min-h-screen bg-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight">Monitor Fiscal</h1>
            <p className="text-slate-500 mt-1">Gestão de NFC-e (Modelo 65) emitidas.</p>
          </div>
          <button 
            onClick={fetchNotas}
            className="bg-white hover:bg-slate-50 text-slate-900 font-bold px-6 py-3 rounded-2xl transition-all border border-slate-200 shadow-sm flex items-center gap-2"
          >
            <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Atualizar
          </button>
        </div>

        <div className="bg-white rounded-[2.5rem] shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/50 border-b border-slate-100">
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">ID / Venda</th>
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Chave de Acesso</th>
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Protocolo</th>
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">Status SEFAZ</th>
                  <th className="p-6 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {notas.map((nota: any) => (
                  <tr key={nota.id} className="hover:bg-slate-50/50 transition-colors group">
                    <td className="p-6 font-bold text-slate-900">#{nota.id} <span className="text-slate-400 font-medium block text-xs">Venda #{nota.venda_id}</span></td>
                    <td className="p-6 font-mono text-xs text-slate-500">{nota.chave_acesso || 'Pendente'}</td>
                    <td className="p-6 text-sm text-slate-600 font-medium">{nota.protocolo || '-'}</td>
                    <td className="p-6">
                      <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest ${
                        nota.status_sefaz === '100' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'
                      }`}>
                        {nota.status_sefaz === '100' ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        {nota.status_sefaz === '100' ? 'Autorizada' : 'Erro / Cancelada'}
                      </div>
                    </td>
                    <td className="p-6 text-right">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-2 hover:bg-brand-50 rounded-lg text-brand-600 transition-all shadow-sm border border-brand-100" title="Ver XML">
                          <FileText className="w-4 h-4" />
                        </button>
                        <button className="p-2 hover:bg-slate-900 rounded-lg text-white transition-all shadow-lg" title="Imprimir DANFE">
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {notas.length === 0 && !loading && (
                  <tr>
                    <td colSpan={5} className="p-20 text-center text-slate-400 font-medium">Nenhuma nota emitida ainda.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
