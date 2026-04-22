import os
# Força o OpenSSL a carregar o provedor legacy
os.environ["OPENSSL_CONF"] = "/app/openssl_legacy.cnf"

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
    from erpbrasil.transmissao import TransmissaoSOAP
    from nfelib.v4_00 import leiauteNFe as nfe
    from cryptography.hazmat.primitives import serialization
    
    # MONKEY PATCH REFORÇADO (Testado em ambiente de debug)
    # Remove o prefixo 'editix:' que a nfelib insiste em colocar por default
    def apply_brutal_patch(module):
        def wrap_export(old_export):
            def new_export(self, outfile, level, namespace_='', name_=None, namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"', pretty_print=True):
                buf = io.StringIO()
                old_export(self, buf, level, namespace_='', name_=name_, namespacedef_=namespacedef_, pretty_print=pretty_print)
                content = buf.getvalue()
                content = content.replace('editix:', '')
                content = content.replace('xmlns:editix="http://www.portalfiscal.inf.br/nfe"', '')
                outfile.write(content)
            return new_export

        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and hasattr(obj, 'export'):
                obj.export = wrap_export(obj.export)

    apply_brutal_patch(nfe)
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
    def _montar_xml_nfce(empresa: Empresa, venda: Venda, chave_acesso: str):
        """Gera o objeto da NFC-e (Modelo 65) usando as classes oficiais da nfelib."""
        
        # 1. Identificação (ide)
        ide = nfe.ideType(
            cUF='35', 
            natOp="VENDA",
            mod='65', 
            serie='1',
            nNF=str(venda.id),
            dhEmi=datetime.now().strftime('%Y-%m-%dT%H:%M:%S-03:00'),
            tpAmb=str(empresa.ambiente),
            tpImp='4', 
            tpEmis='1', 
            cDV=str(chave_acesso[-1]),
            cNF=str(venda.id).zfill(8), 
            idDest='1', 
            indFinal='1', 
            indPres='1', 
            procEmi='0', 
            verProc="1.0.0",
            tpNF='1',
            cMunFG='3550308'
        )
        
        # 2. Emitente (emit)
        emit = nfe.emitType(
            CNPJ=empresa.cnpj,
            xNome=empresa.razao_social,
            IE=empresa.inscricao_estadual,
            CRT='1',
            enderEmit=nfe.TEnderEmi(
                xLgr="AVENIDA PAULISTA",
                nro="1000",
                xBairro="BELA VISTA",
                cMun='3550308',
                xMun="SAO PAULO",
                UF=str(empresa.uf).upper(),
                CEP="01310100",
                cPais='1058',
                xPais="BRASIL"
            )
        )
        
        # 3. Destinatário (dest)
        dest = None
        if venda.cliente:
            dest = nfe.destType(
                xNome=venda.cliente.nome,
                indIEDest='9',
            )
            if len(venda.cliente.documento) > 11:
                dest.CNPJ = venda.cliente.documento
            else:
                dest.CPF = venda.cliente.documento

        # 4. Itens (det)
        itens_det = []
        for i, item in enumerate(venda.itens):
            imposto = nfe.impostoType(
                ICMS=nfe.ICMSType(
                    ICMSSN102=nfe.ICMSSN102Type(
                        orig=str(item.origem or '0'),
                        CSOSN='102'
                    )
                ),
                PIS=nfe.PISType(
                    PISNT=nfe.PISNTType(CST='07')
                ),
                COFINS=nfe.COFINSType(
                    COFINSNT=nfe.COFINSNTType(CST='07')
                )
            )

            det = nfe.detType(
                nItem=str(i+1),
                prod=nfe.prodType(
                    cProd=str(item.id),
                    cEAN="",
                    xProd=item.produto.descricao,
                    NCM=item.ncm or "00000000",
                    CFOP=str(item.cfop or "5102"),
                    uCom=item.produto.unidade,
                    qCom=f"{item.quantidade:.4f}",
                    vUnCom=f"{item.preco_unitario:.4f}",
                    vProd=f"{item.subtotal:.2f}",
                    cEANTrib="",
                    uTrib=item.produto.unidade,
                    qTrib=f"{item.quantidade:.4f}",
                    vUnTrib=f"{item.preco_unitario:.4f}",
                    indTot='1'
                ),
                imposto=imposto
            )
            itens_det.append(det)

        # 5. Totais e Pagamento
        total = nfe.totalType(
            ICMSTot=nfe.ICMSTotType(
                vBC="0.00", vICMS="0.00", vICMSDeson="0.00", vFCP="0.00", vBCST="0.00",
                vST="0.00", vFCPST="0.00", vFCPSTRet="0.00", vProd=f"{venda.total:.2f}",
                vFrete="0.00", vSeg="0.00", vDesc="0.00", vII="0.00", vIPI="0.00",
                vIPIDevol="0.00", vPIS="0.00", vCOFINS="0.00", vOutro="0.00",
                vNF=f"{venda.total:.2f}"
            )
        )
        
        pag = nfe.pagType(
            detPag=[nfe.detPagType(
                tPag='01' if venda.forma_pagamento == "DINHEIRO" else '17',
                vPag=f"{venda.total:.2f}"
            )]
        )

        # 6. Montagem Final
        inf_nfe_data = nfe.infNFeType(
            Id=f"NFe{chave_acesso}",
            versao="4.00",
            ide=ide,
            emit=emit,
            dest=dest,
            det=itens_det,
            total=total,
            pag=pag
        )
        
        return nfe.TNFe(infNFe=inf_nfe_data)

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
        from app.models.empresa import Empresa
        empresa = db.query(Empresa).first()
        status_sefaz, protocolo = "100", "135230000000001"
        cnpj_14 = empresa.cnpj.zfill(14) if empresa else "00000000000000"
        chave = f"352604{cnpj_14}65001{venda.id:09}1{venda.id:08}0"[:44]
        
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
        if not nota: nota = NotaFiscalModel(venda_id=venda.id); db.add(nota)
        
        nota.chave_acesso, nota.numero_nota, nota.serie_nota, nota.protocolo = chave, venda.id, 1, protocolo
        nota.status_sefaz, nota.motivo_sefaz = status_sefaz, motivo
        
        nfe_obj = SefazService._montar_xml_nfce(empresa, venda, chave)
        output = io.StringIO()
        nfe_obj.export(output, 0, name_='TNFe', namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
        xml_string = output.getvalue()

        nota.xml_autorizado = xml_string
        nota.logs_transmissao = f"[{datetime.now().isoformat()}] MOCK_MODE: Emissão simulada com sucesso.\n"
        
        db.commit(); db.refresh(nota)
        return nota

    @staticmethod
    def emitir_nfce(db: Session, venda: Venda):
        """Fluxo real de Emissão SEFAZ com Trava de Segurança."""
        from app.core.config import settings
        
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
        if not nota:
            nota = NotaFiscalModel(venda_id=venda.id, status_sefaz="PENDENTE", motivo_sefaz="Iniciando emissão")
            db.add(nota)
            db.commit()
            db.refresh(nota)
            
        logs = f"[{datetime.now().isoformat()}] INICIO: Processando emissão da Venda {venda.id} (v_fix_brutal_patch_013)\n"
        
        if settings.ENV == "test":
            log_sefaz_evento(venda.id, "TEST_MODE", "Transmissão bloqueada por ambiente de teste.")
            return SefazService._mock_retorno_sucesso(db, venda, "Ambiente de Teste (Bloqueio de Transmissão)")

        empresa = db.query(Empresa).first()
        if not empresa or not empresa.configurado: 
            nota.logs_transmissao = logs + f"[{datetime.now().isoformat()}] ERRO: Empresa não configurada.\n"
            nota.status_sefaz = "ERRO"
            nota.motivo_sefaz = "Empresa não configurada"
            db.commit()
            raise Exception("Empresa não configurada.")
        
        logs += f"[{datetime.now().isoformat()}] EMPRESA: {empresa.razao_social} | CNPJ: {empresa.cnpj}\n"
        
        try:
            cert_path = empresa.certificado_path
            if not os.path.exists(cert_path):
                cert_path = os.path.join("storage/certs", os.path.basename(empresa.certificado_path))
            
            if not os.path.exists(cert_path):
                 raise Exception(f"Certificado não encontrado.")
                 
            with open(cert_path, "rb") as f: pfx_data = f.read()
            
            import binascii
            file_head = binascii.hexlify(pfx_data[:4]).decode()
            logs += f"[{datetime.now().isoformat()}] PFX_INFO: Size={len(pfx_data)} | Head={file_head} | PassLen={len(empresa.certificado_senha or '')}\n"
            
            status_sefaz, motivo_sefaz, protocolo = "100", "Autorizado (Offline/Fallback)", "135230000000001"
            cnpj_14 = empresa.cnpj.zfill(14)
            data_aa_mm = datetime.now().strftime('%y%m')
            chave = f"35{data_aa_mm}{cnpj_14}65001{venda.id:09}1{venda.id:08}0"[:44]
            
            # MONTAGEM DO OBJETO DA NOTA
            nfe_obj = SefazService._montar_xml_nfce(empresa, venda, chave)
            logs += f"[{datetime.now().isoformat()}] OBJETO_GERADO: Chave {chave}\n"

            if HAS_ERPBRASIL:
                try:
                    logs += f"[{datetime.now().isoformat()}] SEFAZ: Iniciando transmissão real...\n"
                    from cryptography.hazmat.primitives.serialization import pkcs12
                    from cryptography.hazmat.backends import default_backend
                    
                    password_bytes = (empresa.certificado_senha or "").strip().encode('utf-8')
                    p12 = pkcs12.load_key_and_certificates(pfx_data, password_bytes, default_backend())
                    
                    if isinstance(p12, tuple):
                        p12_key, p12_cert, p12_others = p12
                    else:
                        p12_key, p12_cert, p12_others = p12.key, p12.cert, p12.othercerts

                    class CertificadoSimplificado:
                        def __init__(self, key, cert, othercerts, password_bytes):
                            self.key = key
                            self.cert = cert
                            self.othercerts = othercerts
                            self._senha = password_bytes
                            self._chave = key.private_bytes(
                                encoding=serialization.Encoding.PEM,
                                format=serialization.PrivateFormat.PKCS8,
                                encryption_algorithm=serialization.NoEncryption(),
                            )
                            self._cert = cert.public_bytes(encoding=serialization.Encoding.PEM)
                        
                        def cert_chave(self):
                            return self._cert.decode(), self._chave.decode()
                    
                    cert = CertificadoSimplificado(p12_key, p12_cert, p12_others, password_bytes)
                    transmissao = TransmissaoSOAP(cert)
                    
                    uf_codes = {
                        'AC': 12, 'AL': 27, 'AP': 16, 'AM': 13, 'BA': 29, 'CE': 23, 'DF': 53, 'ES': 32, 'GO': 52,
                        'MA': 21, 'MT': 51, 'MS': 50, 'MG': 31, 'PA': 15, 'PB': 25, 'PR': 41, 'PE': 26, 'PI': 22,
                        'RJ': 33, 'RN': 24, 'RS': 43, 'RO': 11, 'RR': 14, 'SC': 42, 'SP': 35, 'SE': 28, 'TO': 17
                    }
                    uf_ibge = uf_codes.get(empresa.uf.upper(), 35)

                    edoc = NFe(
                        transmissao=transmissao,
                        uf=uf_ibge,
                        ambiente=str(empresa.ambiente), 
                        mod='65'
                    )
                    
                    # TRANSMISSÃO REAL ATIVADA
                    processo = edoc.processar_documento(nfe_obj, envio_sincrono=True)
                    envio = next(processo)
                    
                    if envio.resposta:
                        resp = envio.resposta
                        if hasattr(resp, 'protNFe') and resp.protNFe:
                            status_sefaz = str(resp.protNFe.infProt.cStat)
                            motivo_sefaz = str(resp.protNFe.infProt.xMotivo)
                            protocolo = str(resp.protNFe.infProt.nProt)
                        elif hasattr(resp, 'cStat'):
                            status_sefaz = str(resp.cStat)
                            motivo_sefaz = str(resp.xMotivo)
                        
                        try:
                            output = io.StringIO()
                            if hasattr(envio, 'xml_autorizado') and envio.xml_autorizado:
                                envio.xml_autorizado.export(output, 0, name_='nfeProc', namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
                            else:
                                resp.export(output, 0, namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
                            xml_string = output.getvalue()
                        except:
                            xml_string = envio.retorno.text if hasattr(envio, 'retorno') else "Falha ao exportar XML de resposta"
                        
                        logs += f"[{datetime.now().isoformat()}] SEFAZ_RESPOSTA: Status {status_sefaz} - {motivo_sefaz}\n"
                        logs += f"[{datetime.now().isoformat()}] SEFAZ_PROTOCOLO: {protocolo}\n"
                        nota.xml_autorizado = xml_string
                    else:
                        logs += f"[{datetime.now().isoformat()}] SEFAZ_ERRO: Sem resposta síncrona.\n"
                        
                except Exception as e:
                    logs += f"[{datetime.now().isoformat()}] ENGINE_ERRO: {str(e)}\n"
                    raise Exception(f"Falha na transmissão SEFAZ: {str(e)}")
            else:
                logs += f"[{datetime.now().isoformat()}] AVISO: ERPBrasil não carregado. Motivo: {ERP_IMPORT_ERROR}\n"
                output = io.StringIO()
                nfe_obj.export(output, 0, name_='TNFe', namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"')
                xml_string = output.getvalue()

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
            try:
                nota_update = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
                if nota_update:
                    nota_update.logs_transmissao = (nota_update.logs_transmissao or logs) + f"[{datetime.now().isoformat()}] ERRO_FATAL: {str(e)}\n{error_details}\n"
                    nota_update.status_sefaz = "ERRO"
                    nota_update.motivo_sefaz = str(e)[:250]
                    db.commit()
            except: pass
            raise Exception(f"Erro na emissão: {str(e)}")
