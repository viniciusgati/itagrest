'use client'

import { useState, useEffect } from 'react'
import { 
  Building2, 
  MapPin, 
  ShieldCheck, 
  ChevronRight, 
  ChevronLeft, 
  Upload, 
  Check,
  FileBadge,
  Loader2,
  Lock
} from 'lucide-react'
import api from '@/lib/api'

export default function WizardFiscal() {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  // Form Data
  const [formData, setFormData] = useState({
    cnpj: '',
    razao_social: '',
    nome_fantasia: '',
    inscricao_estadual: '',
    logradouro: '',
    numero: '',
    bairro: '',
    municipio_nome: '',
    uf: '',
    cep: '',
    ambiente: 2, // Default Homologação
    csc_token: '',
    csc_id: '',
    observacoes_nf: '',
    certificado_senha: '',
    pix_chave: ''
  })
  
  const [certificadoFile, setCertificadoFile] = useState<File | null>(null)

  useEffect(() => {
    const loadEmpresa = async () => {
      try {
        const res = await api.get('/empresa/status')
        if (res.data.empresa) {
          setFormData(prev => ({
            ...prev,
            ...res.data.empresa,
            certificado_senha: '' // Não trazemos a senha por segurança
          }))
        }
      } catch (err) {
        console.error("Erro ao carregar dados da empresa", err)
      }
    }
    loadEmpresa()
  }, [])

  const totalSteps = 3

  const nextStep = () => setStep(s => Math.min(s + 1, totalSteps))
  const prevStep = () => setStep(s => Math.max(s - 1, 1))

  const handleFinish = async () => {
    setLoading(true)
    setError('')
    
    try {
      // Limpar máscaras (deixar apenas números)
      const cleanCnpj = formData.cnpj.replace(/\D/g, '')
      const cleanCep = formData.cep.replace(/\D/g, '')

      // 1. Salvar dados da empresa
      await api.post('/empresa/configurar', {
        ...formData,
        cnpj: cleanCnpj,
        cep: cleanCep || null,
        uf: formData.uf || null,
        municipio_nome: formData.municipio_nome || null,
        csc_token: formData.csc_token || null,
        csc_id: formData.csc_id || null
      })

      // 2. Upload do certificado se existir
      if (certificadoFile) {
        const uploadData = new FormData()
        uploadData.append('file', certificadoFile)
        uploadData.append('senha', formData.certificado_senha)

        await api.post('/empresa/upload-certificado', uploadData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      }

      setSuccess(true)
    } catch (err: any) {
      console.error("Erro no Wizard:", err)
      const response = err.response
      
      if (!response) {
        setError('Não foi possível conectar ao servidor. Verifique sua conexão ou se o backend está rodando.')
      } else if (response.status === 500) {
        setError('Erro interno no servidor (500). Por favor, verifique os logs do sistema.')
      } else if (response.status === 422) {
        // Erro de validação do Pydantic
        const detail = response.data?.detail
        if (Array.isArray(detail)) {
          setError(`Erro de validação: ${detail[0]?.msg || 'Dados inválidos'}`)
        } else {
          setError(detail || 'Dados inválidos para processamento.')
        }
      } else {
        setError(response.data?.detail || 'Erro inesperado ao salvar configuração.')
      }
      
      // Se o erro for relacionado ao certificado ou SEFAZ, volta para o passo 3
      if (step < 3) setStep(3)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <div className="bg-white p-12 rounded-[2.5rem] shadow-2xl text-center max-w-md w-full border border-slate-100 animate-in fade-in zoom-in duration-500">
          <div className="w-24 h-24 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-8 animate-bounce">
            <Check className="w-12 h-12 text-emerald-600" />
          </div>
          <h1 className="text-3xl font-black text-slate-900 mb-4 tracking-tight">Ativado com Sucesso!</h1>
          <p className="text-slate-500 mb-8 leading-relaxed">
            Sua configuração fiscal foi concluída. Agora o iTagREST está pronto para emitir suas notas fiscais.
          </p>
          <button 
            onClick={() => window.location.href = '/dashboard'}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-5 rounded-2xl transition-all shadow-lg shadow-emerald-200"
          >
            Ir para o Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4 md:p-10 font-sans selection:bg-brand-100 selection:text-brand-700">
      <div className="max-w-4xl w-full">
        {/* Header & Steps */}
        <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6 px-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-50 text-brand-700 text-xs font-bold rounded-full mb-3 tracking-wider uppercase">
              <ShieldCheck className="w-3.5 h-3.5" /> Ativação Fiscal
            </div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight">Configure sua Empresa</h1>
            <p className="text-slate-500 mt-2">Precisamos desses dados para emitir NFC-e legalmente.</p>
          </div>
          
          <div className="flex items-center gap-2">
            {[1, 2, 3].map((s) => (
              <div 
                key={s}
                className={`h-2.5 rounded-full transition-all duration-500 ${
                  s === step ? 'w-10 bg-brand-600' : s < step ? 'w-6 bg-emerald-500' : 'w-6 bg-slate-200'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Wizard Card */}
        <div className="bg-white rounded-[3rem] shadow-2xl shadow-slate-200/60 border border-slate-100 overflow-hidden min-h-[500px] flex flex-col">
          <div className="p-8 md:p-12 flex-1">
            {error && (
              <div className="mb-8 p-4 bg-red-50 border border-red-100 text-red-600 rounded-2xl text-sm font-semibold animate-shake">
                {error}
              </div>
            )}

            {/* STEP 1: DADOS BÁSICOS */}
            {step === 1 && (
              <div className="space-y-8 animate-in slide-in-from-right-10 duration-500">
                <div className="flex items-center gap-4 mb-2">
                  <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600">
                    <Building2 className="w-6 h-6" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800">Dados do Emitente</h2>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">CNPJ</label>
                    <input 
                      type="text" 
                      placeholder="00.000.000/0000-00"
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                      value={formData.cnpj}
                      onChange={e => setFormData({...formData, cnpj: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">Inscrição Estadual</label>
                    <input 
                      type="text" 
                      placeholder="Isento ou Número"
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                      value={formData.inscricao_estadual}
                      onChange={e => setFormData({...formData, inscricao_estadual: e.target.value})}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-700 ml-1">Razão Social</label>
                  <input 
                    type="text" 
                    placeholder="Nome da sua Empresa LTDA"
                    className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                    value={formData.razao_social}
                    onChange={e => setFormData({...formData, razao_social: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-700 ml-1">Nome Fantasia (Comercial)</label>
                  <input 
                    type="text" 
                    placeholder="Nome do seu Restaurante"
                    className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                    value={formData.nome_fantasia}
                    onChange={e => setFormData({...formData, nome_fantasia: e.target.value})}
                  />
                </div>

                <div className="pt-6 border-t border-slate-100 space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-amber-50 rounded-xl flex items-center justify-center text-amber-600">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-800">Parâmetros Fiscais (NFC-e)</h3>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-slate-700 ml-1">Token CSC</label>
                      <input 
                        type="text" 
                        placeholder="Ex: 00112233..."
                        className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                        value={formData.csc_token}
                        onChange={e => setFormData({...formData, csc_token: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-slate-700 ml-1">ID do CSC</label>
                      <input 
                        type="text" 
                        placeholder="Ex: 000001"
                        className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                        value={formData.csc_id}
                        onChange={e => setFormData({...formData, csc_id: e.target.value})}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">Observações Gerais (Sai no rodapé da Nota)</label>
                    <textarea 
                      placeholder="Ex: Dados bancários para pagamento, frases promocionais, etc."
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium min-h-[100px]"
                      value={formData.observacoes_nf}
                      onChange={e => setFormData({...formData, observacoes_nf: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">Ambiente de Emissão</label>
                    <div className="flex p-1.5 bg-slate-100 rounded-2xl w-full md:w-1/2">
                      <button 
                        onClick={() => setFormData({...formData, ambiente: 2})}
                        className={`flex-1 py-2.5 rounded-xl font-bold text-sm transition-all ${
                          formData.ambiente === 2 ? 'bg-white text-brand-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                        }`}
                      >
                        Homologação (Testes)
                      </button>
                      <button 
                        onClick={() => setFormData({...formData, ambiente: 1})}
                        className={`flex-1 py-2.5 rounded-xl font-bold text-sm transition-all ${
                          formData.ambiente === 1 ? 'bg-white text-orange-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                        }`}
                      >
                        Produção (Real)
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2: ENDEREÇO */}
            {step === 2 && (
              <div className="space-y-8 animate-in slide-in-from-right-10 duration-500">
                <div className="flex items-center gap-4 mb-2">
                  <div className="w-12 h-12 bg-amber-50 rounded-2xl flex items-center justify-center text-amber-600">
                    <MapPin className="w-6 h-6" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800">Onde fica seu restaurante?</h2>
                </div>

                <div className="grid md:grid-cols-3 gap-6">
                  <div className="md:col-span-2 space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">Logradouro (Rua/Av)</label>
                    <input 
                      type="text" 
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                      value={formData.logradouro}
                      onChange={e => setFormData({...formData, logradouro: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">Número</label>
                    <input 
                      type="text" 
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                      value={formData.numero}
                      onChange={e => setFormData({...formData, numero: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">CEP</label>
                    <input 
                      type="text" 
                      placeholder="00000-000"
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                      value={formData.cep}
                      onChange={e => setFormData({...formData, cep: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">Bairro</label>
                    <input 
                      type="text" 
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                      value={formData.bairro}
                      onChange={e => setFormData({...formData, bairro: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-6">
                  <div className="col-span-2 space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">Município</label>
                    <input 
                      type="text" 
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                      value={formData.municipio_nome}
                      onChange={e => setFormData({...formData, municipio_nome: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-slate-700 ml-1">UF</label>
                    <input 
                      type="text" 
                      placeholder="SP"
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium uppercase"
                      value={formData.uf}
                      onChange={e => setFormData({...formData, uf: e.target.value.toUpperCase()})}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: CERTIFICADO & SEFAZ */}
            {step === 3 && (
              <div className="space-y-8 animate-in slide-in-from-right-10 duration-500">
                <div className="flex items-center gap-4 mb-2">
                  <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600">
                    <FileBadge className="w-6 h-6" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800">Certificado Digital (A1)</h2>
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                  {/* File Upload */}
                  <div className="space-y-4">
                    <label className="text-sm font-bold text-slate-700 ml-1">Arquivo .pfx</label>
                    <div 
                      className={`relative h-40 border-2 border-dashed rounded-[2rem] flex flex-col items-center justify-center transition-all ${
                        certificadoFile ? 'bg-emerald-50 border-emerald-300' : 'bg-slate-50 border-slate-200 hover:border-brand-300'
                      }`}
                    >
                      <input 
                        type="file" 
                        accept=".pfx"
                        className="absolute inset-0 opacity-0 cursor-pointer"
                        onChange={e => setCertificadoFile(e.target.files ? e.target.files[0] : null)}
                      />
                      {certificadoFile ? (
                        <>
                          <div className="w-10 h-10 bg-emerald-600 text-white rounded-full flex items-center justify-center mb-2">
                            <Check className="w-6 h-6" />
                          </div>
                          <p className="text-emerald-700 font-bold text-sm truncate max-w-[200px]">{certificadoFile.name}</p>
                        </>
                      ) : (
                        <>
                          <Upload className="w-8 h-8 text-slate-300 mb-2" />
                          <p className="text-slate-400 font-medium text-sm">Clique ou Arraste o PFX</p>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Password & Environment */}
                  <div className="space-y-6">
                    <div className="space-y-2">
                      <label className="text-sm font-bold text-slate-700 ml-1">Senha do Certificado</label>
                      <div className="relative">
                        <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input 
                          type="password" 
                          placeholder="Sua senha"
                          className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-brand-100 focus:border-brand-500 outline-none transition-all font-medium"
                          value={formData.certificado_senha}
                          onChange={e => setFormData({...formData, certificado_senha: e.target.value})}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-bold text-slate-700 ml-1">Ambiente de Emissão</label>
                      <div className="flex p-1.5 bg-slate-100 rounded-2xl">
                        <button 
                          onClick={() => setFormData({...formData, ambiente: 2})}
                          className={`flex-1 py-2.5 rounded-xl font-bold text-sm transition-all ${
                            formData.ambiente === 2 ? 'bg-white text-brand-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                          }`}
                        >
                          Homologação
                        </button>
                        <button 
                          onClick={() => setFormData({...formData, ambiente: 1})}
                          className={`flex-1 py-2.5 rounded-xl font-bold text-sm transition-all ${
                            formData.ambiente === 1 ? 'bg-white text-orange-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                          }`}
                        >
                          Produção
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer Navigation */}
          <div className="p-8 md:px-12 md:py-10 bg-slate-50 flex items-center justify-between">
            <button 
              onClick={prevStep}
              className={`flex items-center gap-2 font-bold text-slate-500 hover:text-slate-900 transition-colors ${
                step === 1 ? 'invisible' : 'visible'
              }`}
            >
              <ChevronLeft className="w-5 h-5" /> Voltar
            </button>

            {step < totalSteps ? (
              <button 
                onClick={nextStep}
                className="bg-slate-900 hover:bg-slate-800 text-white font-black px-10 py-5 rounded-2xl transition-all shadow-xl active:scale-95 flex items-center gap-3"
              >
                Próximo Passo <ChevronRight className="w-5 h-5" />
              </button>
            ) : (
              <button 
                onClick={handleFinish}
                disabled={loading}
                className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-black px-12 py-5 rounded-2xl transition-all shadow-xl shadow-emerald-200 active:scale-95 flex items-center gap-3"
              >
                {loading ? (
                  <Loader2 className="w-6 h-6 animate-spin" />
                ) : (
                  <>Finalizar e Ativar <ShieldCheck className="w-6 h-6" /></>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
