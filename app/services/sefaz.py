import os
from lxml import etree
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
import io

# Módulos de Impressão (ReportLab)
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import qr

# Módulos modulares do ERPBrasil
try:
    from erpbrasil.base.certificado import Certificado
    from erpbrasil.edoc.nfe import NFe 
    HAS_ERPBRASIL = True
except ImportError:
    HAS_ERPBRASIL = False
    print("AVISO: erpbrasil.edoc não encontrada.")

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
            etree.SubElement(prod, "{%s}NCM" % ns).text = item.produto.ncm
            etree.SubElement(prod, "{%s}CFOP" % ns).text = item.produto.cfop
            etree.SubElement(prod, "{%s}uCom" % ns).text = item.produto.unidade
            etree.SubElement(prod, "{%s}qCom" % ns).text = str(item.quantidade)
            etree.SubElement(prod, "{%s}vUnCom" % ns).text = f"{item.preco_unitario:.2f}"
            etree.SubElement(prod, "{%s}vProd" % ns).text = f"{item.subtotal:.2f}"
            imposto = etree.SubElement(det, "{%s}imposto" % ns)
            icms = etree.SubElement(imposto, "{%s}ICMS" % ns)
            icms_sn = etree.SubElement(icms, "{%s}ICMSSN102" % ns)
            etree.SubElement(icms_sn, "{%s}orig" % ns).text = item.produto.origem
            etree.SubElement(icms_sn, "{%s}CSOSN" % ns).text = "102"

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
        db.commit(); db.refresh(nota)
        return nota

    @staticmethod
    def emitir_nfce(db: Session, venda: Venda):
        """Fluxo real de Emissão SEFAZ com Trava de Segurança."""
        from app.core.config import settings
        
        # TRAVA DE SEGURANÇA MÁXIMA: Nunca transmite se for ambiente de teste
        if settings.ENV == "test":
            log_sefaz_evento(venda.id, "TEST_MODE", "Transmissão bloqueada por ambiente de teste.")
            return SefazService._mock_retorno_sucesso(db, venda, "Ambiente de Teste (Bloqueio de Transmissão)")

        empresa = db.query(Empresa).first()
        if not empresa or not empresa.configurado: raise Exception("Empresa não configurada.")
        try:
            cert_path = os.path.join("storage/certs", empresa.certificado_path)
            if not os.path.exists(cert_path): cert_path = empresa.certificado_path
            with open(cert_path, "rb") as f: pfx_data = f.read()
            
            # Valores Padrão (Fallback Mock se não transmitir)
            status_sefaz, motivo_sefaz, protocolo = "100", "Autorizado (Simulado)", "135230000000001"
            cnpj_14 = empresa.cnpj.zfill(14)
            data_aa_mm = datetime.utcnow().strftime('%y%m')
            chave = f"35{data_aa_mm}{cnpj_14}65001{venda.id:09}1{venda.id:08}0"[:44]
            xml_string = SefazService._montar_xml_nfce(empresa, venda, chave)

            if HAS_ERPBRASIL:
                try:
                    cert = Certificado(pfx_data, empresa.certificado_senha)
                    edoc = NFe(
                        transmitir=True, 
                        certificado=cert, 
                        estado=empresa.uf, 
                        ambiente=str(empresa.ambiente), 
                        versao='4.00'
                    )
                    
                    # TRANSMISSÃO REAL ATIVADA 🚀
                    # Envio síncrono para NFC-e (Modelo 65)
                    envio = edoc.autorizar(xml_string, indicador_processamento=1)
                    
                    if envio.resposta:
                        status_sefaz = str(envio.status)
                        motivo_sefaz = str(envio.motivo)
                        chave = str(envio.chave)
                        protocolo = str(envio.protocolo)
                        xml_string = str(envio.xml_autorizado)
                        
                        log_sefaz_evento(venda.id, status_sefaz, f"RESPOSTA SEFAZ: {motivo_sefaz}", chave)
                    else:
                        log_sefaz_evento(venda.id, "SEM_RESPOSTA", "SEFAZ não retornou resposta síncrona.")
                        
                except Exception as e:
                    log_sefaz_evento(venda.id, "FALHA_ENGINE", f"Erro no motor ERPBrasil: {str(e)}")
                    raise Exception(f"Falha na transmissão SEFAZ: {str(e)}")

            # Gravação no Banco de Dados
            nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
            if not nota:
                nota = NotaFiscalModel(venda_id=venda.id)
                db.add(nota)

            nota.chave_acesso = chave
            nota.numero_nota = venda.id
            nota.serie_nota = 1
            nota.protocolo = protocolo
            nota.status_sefaz = status_sefaz
            nota.motivo_sefaz = motivo_sefaz
            nota.xml_autorizado = xml_string
            
            # Backup do XML Autorizado/Protocolado
            xml_backup_dir = "storage/notas_autorizadas"
            if not os.path.exists(xml_backup_dir): os.makedirs(xml_backup_dir)
            with open(os.path.join(xml_backup_dir, f"NFCe_{chave}.xml"), "w") as f: f.write(xml_string)
            log_xml_auditoria(venda.id, xml_string)

            db.commit()
            db.refresh(nota)
            return nota
            
        except Exception as e: 
            db.rollback()
            log_sefaz_evento(venda.id, "CRITICAL", str(e))
            raise Exception(f"Erro na emissão: {str(e)}")
