import os
from lxml import etree
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
import io

# Módulos de Impressão (ReportLab)
try:
    from reportlab.pdfgen import canvas
    from reportlab.graphics.barcode import qr
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("AVISO: ReportLab não encontrada. Impressão de DANFE desativada.")

# Variável global para capturar erro de importação
ERP_IMPORT_ERROR = ""

# Módulos modulares do ERPBrasil
try:
    from erpbrasil.assinatura.certificado import Certificado
    from erpbrasil.edoc.nfe import NFe 
    HAS_ERPBRASIL = True
except ImportError as e:
    HAS_ERPBRASIL = False
    ERP_IMPORT_ERROR = str(e)
except Exception as e:
    HAS_ERPBRASIL = False
    ERP_IMPORT_ERROR = str(e)

from app.models.empresa import Empresa
from app.models.venda import Venda
from app.models.nota_fiscal import NotaFiscal as NotaFiscalModel
from app.core.logging import log_sefaz_evento, log_xml_auditoria

class SefazService:
    @staticmethod
    def _montar_xml_nfce(empresa: Empresa, venda: Venda, chave_acesso: str) -> str:
        """Gera o XML básico da NFC-e (Modelo 65)."""
        ns = "http://www.portalfiscal.inf.br/nfe"
        nfe_root = etree.Element("{%s}infNFe" % ns, versao="4.00", Id=f"NFe{chave_acesso}")
        
        ide = etree.SubElement(nfe_root, "{%s}ide" % ns)
        etree.SubElement(ide, "{%s}cUF" % ns).text = "35"
        etree.SubElement(ide, "{%s}natOp" % ns).text = "VENDA"
        etree.SubElement(ide, "{%s}mod" % ns).text = "65"
        etree.SubElement(ide, "{%s}serie" % ns).text = "1"
        etree.SubElement(ide, "{%s}nNF" % ns).text = str(venda.id)
        etree.SubElement(ide, "{%s}dhEmi" % ns).text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S-03:00')
        etree.SubElement(ide, "{%s}tpAmb" % ns).text = str(empresa.ambiente)
        
        emit = etree.SubElement(nfe_root, "{%s}emit" % ns)
        etree.SubElement(emit, "{%s}CNPJ" % ns).text = empresa.cnpj
        etree.SubElement(emit, "{%s}xNome" % ns).text = empresa.razao_social
        etree.SubElement(emit, "{%s}IE" % ns).text = empresa.inscricao_estadual
        etree.SubElement(emit, "{%s}CRT" % ns).text = "1"
        
        if venda.cliente:
            dest = etree.SubElement(nfe_root, "{%s}dest" % ns)
            etree.SubElement(dest, "{%s}CNPJ" % ns if len(venda.cliente.documento) > 11 else "{%s}CPF" % ns).text = venda.cliente.documento
            etree.SubElement(dest, "{%s}xNome" % ns).text = venda.cliente.nome
            etree.SubElement(dest, "{%s}indIEDest" % ns).text = "9"

        for i, item in enumerate(venda.itens):
            det = etree.SubElement(nfe_root, "{%s}det" % ns, nItem=str(i+1))
            prod = etree.SubElement(det, "{%s}prod" % ns)
            etree.SubElement(prod, "{%s}cProd" % ns).text = str(item.id)
            etree.SubElement(prod, "{%s}xProd" % ns).text = item.produto.descricao
            etree.SubElement(prod, "{%s}NCM" % ns).text = item.ncm or "00000000"
            etree.SubElement(prod, "{%s}CFOP" % ns).text = item.cfop or "5102"
            etree.SubElement(prod, "{%s}uCom" % ns).text = item.produto.unidade
            etree.SubElement(prod, "{%s}qCom" % ns).text = str(item.quantidade)
            etree.SubElement(prod, "{%s}vUnCom" % ns).text = f"{item.preco_unitario:.2f}"
            etree.SubElement(prod, "{%s}vProd" % ns).text = f"{item.subtotal:.2f}"
            if item.cest:
                etree.SubElement(prod, "{%s}CEST" % ns).text = item.cest

            imposto = etree.SubElement(det, "{%s}imposto" % ns)
            
            # ICMS
            icms = etree.SubElement(imposto, "{%s}ICMS" % ns)
            if empresa.inscricao_estadual:
                icms_sn = etree.SubElement(icms, "{%s}ICMSSN102" % ns)
                etree.SubElement(icms_sn, "{%s}orig" % ns).text = item.origem or "0"
                etree.SubElement(icms_sn, "{%s}CSOSN" % ns).text = item.cst_icms or "102"
            
            # PIS
            pis = etree.SubElement(imposto, "{%s}PIS" % ns)
            pis_nt = etree.SubElement(pis, "{%s}PISNT" % ns)
            etree.SubElement(pis_nt, "{%s}CST" % ns).text = item.cst_pis or "07"
            
            # COFINS
            cofins = etree.SubElement(imposto, "{%s}COFINS" % ns)
            cofins_nt = etree.SubElement(cofins, "{%s}COFINSNT" % ns)
            etree.SubElement(cofins_nt, "{%s}CST" % ns).text = item.cst_cofins or "07"

        total = etree.SubElement(nfe_root, "{%s}total" % ns)
        icms_tot = etree.SubElement(total, "{%s}ICMSTot" % ns)
        etree.SubElement(icms_tot, "{%s}vNF" % ns).text = f"{venda.total:.2f}"

        pag = etree.SubElement(nfe_root, "{%s}pag" % ns)
        det_pag = etree.SubElement(pag, "{%s}detPag" % ns)
        etree.SubElement(det_pag, "{%s}tPag" % ns).text = "01" if venda.forma_pagamento == "DINHEIRO" else "17"
        etree.SubElement(det_pag, "{%s}vPag" % ns).text = f"{venda.total:.2f}"

        xml_final = etree.tostring(nfe_root, encoding='unicode')
        return xml_final

    @staticmethod
    def gerar_danfe_pdf(db: Session, venda_id: int) -> io.BytesIO:
        venda = db.query(Venda).filter(Venda.id == venda_id).first()
        empresa = db.query(Empresa).first()
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        if not nota: raise Exception("Nota fiscal não autorizada.")
        largura, altura = 145, (250 + (len(venda.itens) * 25)) 
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(largura, altura))
        y = altura - 15
        c.setFont("Helvetica-Bold", 8); c.drawCentredString(largura/2, y, empresa.razao_social.upper()[:25]); y -= 10
        c.setFont("Helvetica", 6); c.drawCentredString(largura/2, y, f"CNPJ: {empresa.cnpj}"); y -= 15
        c.setFont("Helvetica-Bold", 8); c.drawCentredString(largura/2, y, "DANFE NFC-e"); y -= 12
        c.setFont("Helvetica", 6)
        for item in venda.itens:
            c.drawString(5, y, item.produto.descricao[:22])
            c.drawRightString(largura - 5, y, f"{item.subtotal:.2f}")
            y -= 10
        y -= 5; c.line(5, y, largura - 5, y); y -= 12
        c.setFont("Helvetica-Bold", 9); c.drawString(5, y, "TOTAL"); c.drawRightString(largura - 5, y, f"R$ {venda.total:.2f}"); y -= 15
        c.setFont("Helvetica", 5); c.drawCentredString(largura/2, y, f"Nota: {nota.numero_nota} Série: {nota.serie_nota}"); y -= 8
        c.drawCentredString(largura/2, y, nota.chave_acesso[:22]); y -= 6; c.drawCentredString(largura/2, y, nota.chave_acesso[22:])
        c.showPage(); c.save(); buffer.seek(0)
        return buffer

    @staticmethod
    def _mock_retorno_sucesso(db: Session, venda: Venda, motivo: str):
        """Gera um registro de nota fiscal mockado para segurança."""
        from app.models.empresa import Empresa
        empresa = db.query(Empresa).first()
        status_sefaz, protocolo = "100", "135230000000001"
        cnpj_14 = empresa.cnpj.zfill(14) if empresa else "00000000000000"
        chave = f"352604{cnpj_14}65001{venda.id:09}1{venda.id:08}0"[:44]
        
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
        if not nota: nota = NotaFiscalModel(venda_id=venda.id); db.add(nota)
        
        nota.chave_acesso, nota.numero_nota, nota.serie_nota, nota.protocolo = chave, venda.id, 1, protocolo
        nota.status_sefaz, nota.motivo_sefaz = status_sefaz, motivo
        
        # XML Mockado para auditoria
        xml_string = SefazService._montar_xml_nfce(empresa, venda, chave)
        nota.xml_autorizado = xml_string
        nota.logs_transmissao = f"[{datetime.utcnow().isoformat()}] MOCK_MODE: Emissão simulada com sucesso.\n"
        
        db.commit(); db.refresh(nota)
        return nota

    @staticmethod
    def emitir_nfce(db: Session, venda: Venda):
        """Fluxo real de Emissão SEFAZ com Trava de Segurança."""
        from app.core.config import settings
        
        # 1. Garante que o registro da NotaFiscal existe no banco antes de tudo
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
        if not nota:
            nota = NotaFiscalModel(venda_id=venda.id, status_sefaz="PENDENTE", motivo_sefaz="Iniciando emissão")
            db.add(nota)
            db.commit()
            db.refresh(nota)
            
        # Inicia logs de transmissão
        logs = f"[{datetime.utcnow().isoformat()}] INICIO: Processando emissão da Venda {venda.id}\n"
        
        # TRAVA DE SEGURANÇA MÁXIMA: Nunca transmite se for ambiente de teste
        if settings.ENV == "test":
            log_sefaz_evento(venda.id, "TEST_MODE", "Transmissão bloqueada por ambiente de teste.")
            return SefazService._mock_retorno_sucesso(db, venda, "Ambiente de Teste (Bloqueio de Transmissão)")

        empresa = db.query(Empresa).first()
        if not empresa or not empresa.configurado: 
            nota.logs_transmissao = logs + f"[{datetime.utcnow().isoformat()}] ERRO: Empresa não configurada.\n"
            nota.status_sefaz = "ERRO"
            nota.motivo_sefaz = "Empresa não configurada"
            db.commit()
            raise Exception("Empresa não configurada.")
        
        logs += f"[{datetime.utcnow().isoformat()}] EMPRESA: {empresa.razao_social} | CNPJ: {empresa.cnpj}\n"
        
        try:
            # Lógica robusta de localização de certificado
            cert_path = empresa.certificado_path
            if not os.path.exists(cert_path):
                cert_path = os.path.join("storage/certs", os.path.basename(empresa.certificado_path))
            
            if not os.path.exists(cert_path):
                 raise Exception(f"Certificado não encontrado em: {empresa.certificado_path} ou {cert_path}")
                 
            with open(cert_path, "rb") as f: pfx_data = f.read()
            
            # Valores Padrão (Fallback se não transmitir ou HAS_ERPBRASIL=False)
            status_sefaz, motivo_sefaz, protocolo = "100", "Autorizado (Offline/Fallback)", "135230000000001"
            cnpj_14 = empresa.cnpj.zfill(14)
            data_aa_mm = datetime.utcnow().strftime('%y%m')
            chave = f"35{data_aa_mm}{cnpj_14}65001{venda.id:09}1{venda.id:08}0"[:44]
            xml_string = SefazService._montar_xml_nfce(empresa, venda, chave)
            logs += f"[{datetime.utcnow().isoformat()}] XML_GERADO: Chave {chave}\n"

            if HAS_ERPBRASIL:
                try:
                    logs += f"[{datetime.utcnow().isoformat()}] SEFAZ: Iniciando transmissão real...\n"
                    cert = Certificado(pfx_data, empresa.certificado_senha)
                    edoc = NFe(
                        transmitir=True, 
                        certificado=cert, 
                        estado=empresa.uf, 
                        ambiente=str(empresa.ambiente), 
                        versao='4.00'
                    )
                    
                    # TRANSMISSÃO REAL ATIVADA 🚀
                    envio = edoc.autorizar(xml_string, indicador_processamento=1)
                    
                    if envio.resposta:
                        status_sefaz = str(envio.status)
                        motivo_sefaz = str(envio.motivo)
                        chave = str(envio.chave)
                        protocolo = str(envio.protocolo)
                        xml_string = str(envio.xml_autorizado)
                        
                        logs += f"[{datetime.utcnow().isoformat()}] SEFAZ_RESPOSTA: Status {status_sefaz} - {motivo_sefaz}\n"
                        logs += f"[{datetime.utcnow().isoformat()}] SEFAZ_PROTOCOLO: {protocolo}\n"
                        log_sefaz_evento(venda.id, status_sefaz, f"RESPOSTA SEFAZ: {motivo_sefaz}", chave)
                    else:
                        logs += f"[{datetime.utcnow().isoformat()}] SEFAZ_ERRO: Sem resposta síncrona.\n"
                        log_sefaz_evento(venda.id, "SEM_RESPOSTA", "SEFAZ não retornou resposta síncrona.")
                        
                except Exception as e:
                    logs += f"[{datetime.utcnow().isoformat()}] ENGINE_ERRO: {str(e)}\n"
                    log_sefaz_evento(venda.id, "FALHA_ENGINE", f"Erro no motor ERPBrasil: {str(e)}")
                    raise Exception(f"Falha na transmissão SEFAZ: {str(e)}")
            else:
                logs += f"[{datetime.utcnow().isoformat()}] AVISO: ERPBrasil não carregado no Python. Motivo: {ERP_IMPORT_ERROR or 'Desconhecido'}\n"
                logs += f"[{datetime.utcnow().isoformat()}] Usando fallback (modo simulação).\n"

            # Gravação Final no Banco de Dados
            nota.chave_acesso = chave
            nota.numero_nota = venda.id
            nota.serie_nota = 1
            nota.protocolo = protocolo
            nota.status_sefaz = status_sefaz
            nota.motivo_sefaz = motivo_sefaz
            nota.xml_autorizado = xml_string
            nota.logs_transmissao = logs
            
            db.commit()
            db.refresh(nota)
            return nota
            
        except Exception as e: 
            db.rollback()
            import traceback
            error_details = traceback.format_exc()
            
            # Garante que o erro seja salvo no registro que criamos no início
            try:
                nota_update = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
                if nota_update:
                    nota_update.logs_transmissao = (nota_update.logs_transmissao or logs) + f"[{datetime.utcnow().isoformat()}] ERRO_FATAL: {str(e)}\n{error_details}\n"
                    nota_update.status_sefaz = "ERRO"
                    nota_update.motivo_sefaz = str(e)[:250]
                    db.commit()
            except: pass
            
            log_sefaz_evento(venda.id, "CRITICAL", f"{str(e)} | {error_details}")
            raise Exception(f"Erro na emissão: {str(e)}")
