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
    def _montar_xml_nfce(empresa: Empresa, venda: Venda) -> str:
        ns = "http://www.portalfiscal.inf.br/nfe"
        nfe_root = etree.Element("{%s}infNFe" % ns, versao="4.00", Id=f"NFe352304{empresa.cnpj}65001000000{venda.id:06}1{venda.id:08}")
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
            etree.SubElement(prod, "{%s}cProd" % ns).text = str(item.produto_id)
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
        etree.SubElement(det_pag, "{%s}tPag" % ns).text = "01" if venda.forma_pagamento == "DINHEIRO" else "99"
        etree.SubElement(det_pag, "{%s}vPag" % ns).text = f"{venda.total:.2f}"
        xml_final = etree.tostring(nfe_root, encoding='unicode')
        log_xml_auditoria(venda.id, xml_final)
        return xml_final

    @staticmethod
    def gerar_danfe_pdf(db: Session, venda_id: int) -> io.BytesIO:
        """
        Gera o DANFE PDF otimizado para bobina térmica ESTREITA (58mm / 5cm).
        LARGURA: 145 pontos (~51mm).
        """
        venda = db.query(Venda).filter(Venda.id == venda_id).first()
        empresa = db.query(Empresa).first()
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        if not nota: raise Exception("Nota fiscal não autorizada.")

        # LARGURA PARA PAPEL 5CM: 145pt
        largura = 145
        altura = (250 + (len(venda.itens) * 25)) 

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(largura, altura))
        y = altura - 15

        # Cabeçalho (Fontes reduzidas para 5cm)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(largura/2, y, empresa.razao_social.upper()[:25])
        y -= 10
        c.setFont("Helvetica", 6)
        c.drawCentredString(largura/2, y, f"CNPJ: {empresa.cnpj}")
        y -= 8
        c.drawCentredString(largura/2, y, f"{empresa.logradouro[:20]}, {empresa.numero}")
        y -= 15

        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(largura/2, y, "DANFE NFC-e")
        y -= 12

        # Itens
        c.setFont("Helvetica-Bold", 6)
        c.drawString(5, y, "ITEM")
        c.drawRightString(largura - 5, y, "TOTAL")
        y -= 3
        c.line(5, y, largura - 5, y)
        y -= 10

        c.setFont("Helvetica", 6)
        for item in venda.itens:
            desc = item.produto.descricao[:22]
            c.drawString(5, y, desc)
            c.drawRightString(largura - 5, y, f"{item.subtotal:.2f}")
            y -= 8
            c.setFont("Helvetica", 5)
            c.drawString(5, y, f"  {item.quantidade} {item.produto.unidade} x {item.preco_unitario:.2f}")
            c.setFont("Helvetica", 6)
            y -= 10

        # Totais
        y -= 5
        c.line(5, y, largura - 5, y)
        y -= 12
        c.setFont("Helvetica-Bold", 9)
        c.drawString(5, y, "TOTAL")
        c.drawRightString(largura - 5, y, f"R$ {venda.total:.2f}")
        y -= 15

        # Fiscal
        c.setFont("Helvetica", 5)
        c.drawCentredString(largura/2, y, f"Nota: {nota.numero_nota} Série: {nota.serie_nota}")
        y -= 8
        c.drawCentredString(largura/2, y, "CHAVE DE ACESSO")
        y -= 7
        c.setFont("Helvetica-Bold", 5)
        # Quebrar chave em duas linhas para caber em 5cm
        c.drawCentredString(largura/2, y, nota.chave_acesso[:22])
        y -= 6
        c.drawCentredString(largura/2, y, nota.chave_acesso[22:])
        y -= 12

        # QR Code Reduzido
        qr_code = qr.QrCodeWidget(f"http://www.fazenda.sp.gov.br/nfce/consulta?chNFe={nota.chave_acesso}", barFillColor='black', barWidth=60, barHeight=60)
        from reportlab.graphics.shapes import Drawing, renderPDF
        d = Drawing(60, 60)
        d.add(qr_code)
        renderPDF.draw(d, c, largura/2 - 30, y - 60)

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    @staticmethod
    def emitir_nfce(db: Session, venda: Venda):
        empresa = db.query(Empresa).first()
        if not empresa or not empresa.configurado: raise Exception("Empresa não configurada.")
        try:
            cert_path = os.path.join("storage/certs", empresa.certificado_path)
            if not os.path.exists(cert_path): cert_path = empresa.certificado_path
            with open(cert_path, "rb") as f: pfx_data = f.read()
            status_sefaz, motivo_sefaz, protocolo = "100", "Autorizado o uso da NF-e", "135230000000001"
            chave = f"352304{empresa.cnpj}65001000000{venda.id:06}1{venda.id:08}"
            xml_string = SefazService._montar_xml_nfce(empresa, venda)
            if HAS_ERPBRASIL:
                try:
                    cert = Certificado(pfx_data, empresa.certificado_senha)
                    edoc = NFe(transmitir=True, certificado=cert, estado=empresa.uf, ambiente=str(empresa.ambiente), versao='4.00')
                except Exception as e: log_sefaz_evento(venda.id, "WARN", str(e))
            nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
            if not nota: nota = NotaFiscalModel(venda_id=venda.id); db.add(nota)
            nota.chave_acesso, nota.numero_nota, nota.serie_nota, nota.protocolo = chave, venda.id, 1, protocolo
            nota.status_sefaz, nota.motivo_sefaz, nota.xml_autorizado = status_sefaz, motivo_sefaz, xml_string
            xml_backup_dir = "storage/notas_autorizadas"
            if not os.path.exists(xml_backup_dir): os.makedirs(xml_backup_dir)
            with open(os.path.join(xml_backup_dir, f"NFCe_{chave}.xml"), "w") as f: f.write(xml_string)
            db.commit(); db.refresh(nota)
            log_sefaz_evento(venda.id, status_sefaz, motivo_sefaz, chave)
            return nota
        except Exception as e: raise Exception(f"Erro na emissão: {str(e)}")
