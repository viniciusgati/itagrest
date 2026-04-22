import os
# Força o OpenSSL a carregar o provedor legacy
os.environ["OPENSSL_CONF"] = "/app/openssl_legacy.cnf"

from lxml import etree
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
import io
import binascii
import re
import hashlib

# Módulos de Impressão (ERPBrasil PDF)
try:
    from erpbrasil.edoc.pdf import danfe
    HAS_DANFE_LIB = True
except ImportError:
    HAS_DANFE_LIB = False
    print("AVISO: erpbrasil.edoc.pdf não encontrada. Usando fallback ReportLab.")
    try:
        from reportlab.pdfgen import canvas
        from reportlab.graphics.barcode import qr
        HAS_REPORTLAB = True
    except ImportError:
        HAS_REPORTLAB = False
        print("AVISO: ReportLab não encontrada. Impressão de DANFE desativada.")

# Variável global para capturar erro de importação
ERP_IMPORT_ERROR = ""

def limpar_xml_sefaz(xml_string: str) -> str:
    """Limpa o XML removendo namespaces redundantes e prefixos editix de forma profunda."""
    try:
        # 1. Limpeza de prefixos na base da string
        xml_string = xml_string.replace('editix:', '').replace('xmlns:editix="http://www.portalfiscal.inf.br/nfe"', '')
        
        # 2. Parser lxml para reconstrução
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(xml_string.encode('utf-8'), parser)
        
        # 3. Remoção recursiva de TODOS os atributos xmlns redundantes
        for el in root.iter():
            if el != root:
                # Remove atributos que começam com {http://www.w3.org/2000/xmlns/}
                for attr in list(el.attrib):
                    if 'xmlns' in attr or '{http://www.w3.org/2000/xmlns/}' in attr:
                        del el.attrib[attr]
        
        # 4. Serialização limpa
        xml_limpo = etree.tostring(root, encoding='unicode', pretty_print=False)
        
        # 5. Garantia final de namespace apenas na raiz
        if 'xmlns=' not in xml_limpo.split('>')[0]:
            xml_limpo = xml_limpo.replace('<NFe', '<NFe xmlns="http://www.portalfiscal.inf.br/nfe"', 1)
            xml_limpo = xml_limpo.replace('<enviNFe', '<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe"', 1)
            
        return xml_limpo
    except:
        # Fallback ultra-agressivo via Regex
        xml_string = re.sub(r'\sxmlns="http://www.portalfiscal.inf.br/nfe"(?!>)', '', xml_string)
        return xml_string

# Módulos modulares do ERPBrasil
try:
    from erpbrasil.assinatura.certificado import Certificado
    from erpbrasil.edoc.nfe import NFe 
    from erpbrasil.edoc.nfce import NFCe
    from erpbrasil.edoc.edoc import DocumentoEletronico
    from erpbrasil.transmissao import TransmissaoSOAP
    from nfelib.v4_00 import leiauteNFe as nfe
    from cryptography.hazmat.primitives import serialization
    
    # MONKEY PATCH GLOBAL NA LIB: Intercepta a geração de XML e limpa ANTES de qualquer uso (assinatura ou envio)
    def apply_global_edoc_patch():
        old_method = DocumentoEletronico._generateds_to_string_etree
        def new_method(self, raiz):
            # Gera o XML original da lib
            xml_string, xml_etree = old_method(self, raiz)
            # Aplica nossa limpeza profunda
            xml_string = limpar_xml_sefaz(xml_string)
            # Reconstrói o etree para a lib não se perder
            xml_etree = etree.fromstring(xml_string.encode('utf-8'))
            return xml_string, xml_etree
        DocumentoEletronico._generateds_to_string_etree = new_method
    
    apply_global_edoc_patch()
    HAS_ERPBRASIL = True
except ImportError as e:
    HAS_ERPBRASIL = False
    ERP_IMPORT_ERROR = str(e)
    print(f"ERRO CRÍTICO: Bibliotecas ERPBrasil não carregadas: {e}")

from app.models.venda import Venda
from app.models.nota_fiscal import NotaFiscal as NotaFiscalModel
from app.models.empresa import Empresa

def log_sefaz_evento(venda_id: int, tipo: str, mensagem: str):
    print(f"[{datetime.now().isoformat()}] [VENDA:{venda_id}] [{tipo}] {mensagem}")

class SefazService:
    @staticmethod
    def _montar_xml_nfce(empresa: Empresa, venda: Venda, chave_acesso: str):
        """Gera o objeto da NFC-e (Modelo 65) usando as classes oficiais da nfelib."""
        
        ibge_cidade = empresa.municipio_ibge if empresa.municipio_ibge else '3550308'
        
        ide = nfe.ideType(
            cUF='35', natOp="VENDA", mod='65', serie='1', nNF=str(venda.id),
            dhEmi=datetime.now().strftime('%Y-%m-%dT%H:%M:%S-03:00'),
            tpAmb=str(empresa.ambiente), tpImp='4', tpEmis='1', cDV=str(chave_acesso[-1]),
            cNF=str(venda.id).zfill(8), idDest='1', indFinal='1', indPres='1', procEmi='0', verProc="1.0.0", tpNF='1',
            cMunFG=ibge_cidade
        )
        emit = nfe.emitType(
            CNPJ=empresa.cnpj, xNome=empresa.razao_social, IE=empresa.inscricao_estadual, CRT='1',
            enderEmit=nfe.TEnderEmi(
                xLgr=empresa.logradouro.upper() if empresa.logradouro else "RUA",
                nro=empresa.numero if empresa.numero else "S/N",
                xBairro=empresa.bairro.upper() if empresa.bairro else "BAIRRO",
                cMun=ibge_cidade,
                xMun=empresa.municipio_nome.upper() if empresa.municipio_nome else "CIDADE",
                UF=str(empresa.uf).upper(), CEP=empresa.cep if empresa.cep else "01000000",
                cPais='1058', xPais="BRASIL"
            )
        )
        dest = None
        if venda.cliente:
            dest = nfe.destType(xNome=venda.cliente.nome, indIEDest='9')
            if len(venda.cliente.documento) > 11: dest.CNPJ = venda.cliente.documento
            else: dest.CPF = venda.cliente.documento
        itens_det = []
        for i, item in enumerate(venda.itens):
            det = nfe.detType(
                nItem=str(i+1),
                prod=nfe.prodType(
                    cProd=str(item.id), xProd=item.produto.descricao, NCM=item.ncm or "22021000", CFOP="5102",
                    uCom=item.produto.unidade, qCom=f"{item.quantidade:.4f}", vUnCom=f"{item.preco_unitario:.4f}",
                    vProd=f"{item.subtotal:.2f}", uTrib=item.produto.unidade, qTrib=f"{item.quantidade:.4f}",
                    vUnTrib=f"{item.preco_unitario:.4f}", indTot='1'
                ),
                imposto=nfe.impostoType(
                    ICMS=nfe.ICMSType(ICMSSN102=nfe.ICMSSN102Type(orig=str(item.origem or '0'), CSOSN='102')),
                    PIS=nfe.PISType(PISNT=nfe.PISNTType(CST='07')),
                    COFINS=nfe.COFINSType(COFINSNT=nfe.COFINSNTType(CST='07'))
                )
            )
            itens_det.append(det)
        total = nfe.totalType(ICMSTot=nfe.ICMSTotType(vBC="0.00", vICMS="0.00", vICMSDeson="0.00", vFCP="0.00", vBCST="0.00", vST="0.00", vFCPST="0.00", vFCPSTRet="0.00", vProd=f"{venda.total:.2f}", vFrete="0.00", vSeg="0.00", vDesc="0.00", vII="0.00", vIPI="0.00", vIPIDevol="0.00", vPIS="0.00", vCOFINS="0.00", vOutro="0.00", vNF=f"{venda.total:.2f}"))
        pag = nfe.pagType(detPag=[nfe.detPagType(tPag='01' if venda.forma_pagamento == "DINHEIRO" else '17', vPag=f"{venda.total:.2f}")])
        inf_nfe_data = nfe.infNFeType(Id=f"NFe{chave_acesso}", versao="4.00", ide=ide, emit=emit, dest=dest, det=itens_det, total=total, pag=pag)
        nota_obj = nfe.TNFe(infNFe=inf_nfe_data)
        if empresa.csc_token and empresa.csc_id:
            url_base = "https://www.nfce.fazenda.sp.gov.br/qrcode?p=" if empresa.ambiente == 1 else "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode?p="
            pre_hash = f"{chave_acesso}|2|{empresa.ambiente}|{empresa.csc_id}"
            full_str = pre_hash + empresa.csc_token
            cHash = hashlib.sha1(full_str.encode()).hexdigest().upper()
            nota_obj.infNFeSupl = nfe.infNFeSuplType(qrCode=f"{url_base}{pre_hash}|{cHash}", urlChave=url_base.replace("qrcode", "consulta"))
        else:
            nota_obj.infNFeSupl = nfe.infNFeSuplType(qrCode="http://sefaz.sp.gov.br", urlChave="http://sefaz.sp.gov.br")
        return nota_obj

    @staticmethod
    def gerar_danfe_pdf(db: Session, venda_id: int) -> io.BytesIO:
        """Gera o PDF da DANFE usando erpbrasil.edoc.pdf."""
        venda = db.query(Venda).filter(Venda.id == venda_id).first()
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        if not nota or not nota.xml_autorizado: raise Exception("Nota fiscal não autorizada ou XML não encontrado.")
        if HAS_DANFE_LIB:
            try:
                xml_content = nota.xml_autorizado.encode('utf-8')
                o_danfe = danfe.Danfe(xml=xml_content, logo='')
                return io.BytesIO(o_danfe.output())
            except Exception as e: print(f"Erro ao usar erpbrasil.edoc.pdf: {e}")
        largura, altura = 145, (250 + (len(venda.itens) * 25)) 
        buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=(largura, altura)); y = altura - 15; empresa = db.query(Empresa).first()
        c.setFont("Helvetica-Bold", 8); c.drawCentredString(largura/2, y, empresa.razao_social.upper()[:25]); y -= 10
        c.setFont("Helvetica", 6); c.drawCentredString(largura/2, y, f"CNPJ: {empresa.cnpj}"); y -= 15
        c.setFont("Helvetica-Bold", 8); c.drawCentredString(largura/2, y, "DANFE NFC-e"); y -= 12
        for item in venda.itens:
            c.setFont("Helvetica", 6); c.drawString(5, y, item.produto.descricao[:22]); c.drawRightString(largura - 5, y, f"{item.subtotal:.2f}"); y -= 10
        y -= 5; c.line(5, y, largura - 5, y); y -= 12
        c.setFont("Helvetica-Bold", 9); c.drawString(5, y, "TOTAL"); c.drawRightString(largura - 5, y, f"R$ {venda.total:.2f}"); y -= 15
        c.setFont("Helvetica", 5); c.drawCentredString(largura/2, y, f"Nota: {nota.numero_nota} Série: {nota.serie_nota}"); y -= 8
        c.drawCentredString(largura/2, y, nota.chave_acesso[:22]); y -= 6; c.drawCentredString(largura/2, y, nota.chave_acesso[22:])
        c.showPage(); c.save(); buffer.seek(0); return buffer

    @staticmethod
    def _mock_retorno_sucesso(db: Session, venda: Venda, motivo: str):
        """Simula sucesso na emissão para testes automatizados."""
        from app.models.empresa import Empresa
        empresa = db.query(Empresa).first()
        status_sefaz, protocolo = "100", "135230000000001"
        cnpj_14 = empresa.cnpj.zfill(14); data_aa_mm = datetime.now().strftime('%y%m')
        chave = f"35{data_aa_mm}{cnpj_14}65001{venda.id:09}1{venda.id:08}0"[:44]
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
        if not nota: nota = NotaFiscalModel(venda_id=venda.id); db.add(nota)
        nota.chave_acesso, nota.numero_nota, nota.serie_nota, nota.protocolo = chave, venda.id, 1, protocolo
        nota.status_sefaz, nota.motivo_sefaz = status_sefaz, motivo
        nfe_obj = SefazService._montar_xml_nfce(empresa, venda, chave)
        output = io.StringIO(); nfe_obj.export(output, 0, name_='NFe', namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
        xml_string = limpar_xml_sefaz(output.getvalue())
        nota.xml_enviado, nota.xml_autorizado = xml_string, xml_string
        nota.logs_transmissao = f"[{datetime.now().isoformat()}] MOCK_MODE: Sucesso.\n"; db.commit(); db.refresh(nota); return nota

    @staticmethod
    def emitir_nfce(db: Session, venda: Venda):
        """Fluxo real de Emissão SEFAZ."""
        from app.core.config import settings
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
        if not nota:
            nota = NotaFiscalModel(venda_id=venda.id, status_sefaz="PENDENTE", motivo_sefaz="Iniciando emissão")
            db.add(nota); db.commit(); db.refresh(nota)
        logs = f"[{datetime.now().isoformat()}] INICIO: Emissão Venda {venda.id}\n"
        if settings.ENV == "test": return SefazService._mock_retorno_sucesso(db, venda, "Ambiente de Teste")
        empresa = db.query(Empresa).first()
        if not empresa or not empresa.configurado: raise Exception("Empresa não configurada.")
        try:
            cert_path = empresa.certificado_path
            if not os.path.exists(cert_path): cert_path = os.path.join("storage/certs", os.path.basename(empresa.certificado_path))
            with open(cert_path, "rb") as f: pfx_data = f.read()
            password_bytes = (empresa.certificado_senha or "").strip().encode('utf-8')
            status_sefaz, motivo_sefaz, protocolo = None, None, None
            cnpj_14 = empresa.cnpj.zfill(14); data_aa_mm = datetime.now().strftime('%y%m')
            chave = f"35{data_aa_mm}{cnpj_14}65001{venda.id:09}1{venda.id:08}0"[:44]
            nfe_obj = SefazService._montar_xml_nfce(empresa, venda, chave)
            if HAS_ERPBRASIL:
                try:
                    from cryptography.hazmat.primitives.serialization import pkcs12
                    from cryptography.hazmat.backends import default_backend
                    p12 = pkcs12.load_key_and_certificates(pfx_data, password_bytes, default_backend())
                    if isinstance(p12, tuple): p12_key, p12_cert, p12_others = p12
                    else: p12_key, p12_cert, p12_others = p12.key, p12.cert, p12.othercerts
                    class CertificadoSimplificado:
                        def __init__(self, key, cert, othercerts, pw):
                            self.key, self.cert, self.othercerts, self._senha = key, cert, othercerts, pw
                            self._chave = key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
                            self._cert = cert.public_bytes(encoding=serialization.Encoding.PEM)
                        def cert_chave(self): return self._cert.decode(), self._chave.decode()
                    cert = CertificadoSimplificado(p12_key, p12_cert, p12_others, password_bytes)
                    transmissao = TransmissaoSOAP(cert)
                    uf_ibge = {'AC':12,'AL':27,'AP':16,'AM':13,'BA':29,'CE':23,'DF':53,'ES':32,'GO':52,'MA':21,'MT':51,'MS':50,'MG':31,'PA':15,'PB':25,'PR':41,'PE':26,'PI':22,'RJ':33,'RN':24,'RS':43,'RO':11,'RR':14,'SC':42,'SP':35,'SE':28,'TO':17}.get(empresa.uf.upper(), 35)
                    edoc = NFCe(transmissao=transmissao, uf=uf_ibge, ambiente=str(empresa.ambiente), mod='65', csc_token=empresa.csc_id, csc_code=empresa.csc_token, envio_sincrono=True)
                    
                    logs += f"[{datetime.now().isoformat()}] SEFAZ: Transmitindo...\n"
                    processo = edoc.processar_documento(nfe_obj, envio_sincrono=True)
                    envio = next(processo)
                    
                    if hasattr(envio, 'retorno'):
                        nota.xml_recebido = envio.retorno.text
                        logs += f"[{datetime.now().isoformat()}] SOAP_RESPONSE: {envio.retorno.text[:1000]}\n"
                    
                    if envio.resposta:
                        resp = envio.resposta
                        if hasattr(resp, 'protNFe') and resp.protNFe:
                            status_sefaz, motivo_sefaz, protocolo = str(resp.protNFe.infProt.cStat), str(resp.protNFe.infProt.xMotivo), str(resp.protNFe.infProt.nProt)
                            if hasattr(resp.protNFe.infProt, 'chNFe'): chave = str(resp.protNFe.infProt.chNFe)
                        elif hasattr(resp, 'cStat'):
                            status_sefaz, motivo_sefaz = str(resp.cStat), str(resp.xMotivo)
                        
                        logs += f"[{datetime.now().isoformat()}] SEFAZ_RESPOSTA: {status_sefaz} - {motivo_sefaz}\n"
                        if hasattr(envio, 'xml_autorizado') and envio.xml_autorizado:
                            xml_string = etree.tostring(envio.xml_autorizado, encoding='unicode')
                            nota.xml_autorizado = limpar_xml_sefaz(xml_string)
                        else:
                            out_resp = io.StringIO(); resp.export(out_resp, 0, namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
                            nota.xml_autorizado = limpar_xml_sefaz(out_resp.getvalue())

                    # SALVA XML ENVIADO (Agora garantido limpo pelo patch global)
                    out_env = io.StringIO(); nfe_obj.export(out_env, 0, name_='NFe', namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
                    nota.xml_enviado = out_env.getvalue()

                except Exception as e:
                    logs += f"[{datetime.now().isoformat()}] ERRO_LIB: {str(e)}\n"
                    out_err = io.StringIO(); nfe_obj.export(out_err, 0, name_='NFe', namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
                    nota.xml_enviado = out_err.getvalue(); raise e

            nota.chave_acesso, nota.numero_nota, nota.protocolo = chave, venda.id, protocolo
            nota.status_sefaz, nota.motivo_sefaz, nota.logs_transmissao = status_sefaz, motivo_sefaz, logs
            db.commit(); return nota
        except Exception as e: 
            db.rollback()
            nota_update = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
            if nota_update:
                nota_update.logs_transmissao = (nota_update.logs_transmissao or "") + logs + f"[{datetime.now().isoformat()}] ERRO_FATAL: {str(e)}\n"
                nota_update.status_sefaz, nota_update.motivo_sefaz = "ERRO", str(e); db.commit()
            raise e
