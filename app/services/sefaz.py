import os, io, binascii, re, hashlib, tempfile, requests
from reportlab.pdfgen import canvas
os.environ["OPENSSL_CONF"] = "/app/openssl_legacy.cnf"
from lxml import etree
from sqlalchemy.orm import Session
from datetime import datetime
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from app.models.venda import Venda
from app.models.nota_fiscal import NotaFiscal as NotaFiscalModel
from app.models.empresa import Empresa

class SefazService:
    @staticmethod
    def calcular_dv(chave_43):
        pesos = [2, 3, 4, 5, 6, 7, 8, 9]
        soma = 0
        for i, digito in enumerate(reversed(chave_43)):
            soma += int(digito) * pesos[i % len(pesos)]
        resto = soma % 11
        return 0 if resto in [0, 1] else 11 - resto

    @staticmethod
    def _gerar_xml_limpo(empresa: Empresa, venda: Venda, chave: str, numero_nf: int) -> str:
        from datetime import timezone, timedelta
        dh_obj = datetime.now(timezone(timedelta(hours=-3)))
        dh = dh_obj.strftime('%Y-%m-%dT%H:%M:%S-03:00')
        ibge = empresa.municipio_ibge or "3550308"
        url = "https://www.nfce.fazenda.sp.gov.br/qrcode" if empresa.ambiente == 1 else "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode"
        
        # QR Code Rigoroso com ID Token sem zeros à esquerda
        id_token = str(int(empresa.csc_id or 1))
        p = f"{chave}|2|{empresa.ambiente}|{id_token}"
        cHash = hashlib.sha1((p + (empresa.csc_token or "")).encode()).hexdigest().upper()
        qr = f"{url}?p={p}|{cHash}"
        
        xml = f'<NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe versao="4.00" Id="NFe{chave}">'
        # nNF agora usa o numero_nf passado e não o venda.id
        xml += f'<ide><cUF>35</cUF><cNF>{str(numero_nf).zfill(8)}</cNF><natOp>VENDA</natOp><mod>65</mod><serie>1</serie><nNF>{numero_nf}</nNF><dhEmi>{dh}</dhEmi><tpNF>1</tpNF><idDest>1</idDest><cMunFG>{ibge}</cMunFG><tpImp>4</tpImp><tpEmis>1</tpEmis><cDV>{chave[-1]}</cDV><tpAmb>{empresa.ambiente}</tpAmb><finNFe>1</finNFe><indFinal>1</indFinal><indPres>1</indPres><procEmi>0</procEmi><verProc>1.0.0</verProc></ide>'
        xml += f'<emit><CNPJ>{empresa.cnpj}</CNPJ><xNome>{empresa.razao_social}</xNome><enderEmit><xLgr>{empresa.logradouro or "RUA"}</xLgr><nro>{empresa.numero or "SN"}</nro><xBairro>{empresa.bairro or "BAIRRO"}</xBairro><cMun>{ibge}</cMun><xMun>{empresa.municipio_nome or "CIDADE"}</xMun><UF>{empresa.uf or "SP"}</UF><CEP>{empresa.cep or "01000000"}</CEP><cPais>1058</cPais><xPais>BRASIL</xPais></enderEmit><IE>{empresa.inscricao_estadual}</IE><CRT>1</CRT></emit>'
        if venda.cliente:
            tag = "CNPJ" if len(venda.cliente.documento) > 11 else "CPF"
            xml += f'<dest><{tag}>{venda.cliente.documento}</{tag}><xNome>{venda.cliente.nome}</xNome><indIEDest>9</indIEDest></dest>'
        
        for i, item in enumerate(venda.itens):
            x_prod = item.produto.descricao
            if i == 0 and empresa.ambiente == 2:
                x_prod = "NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
            xml += f'<det nItem="{i+1}"><prod><cProd>{item.id}</cProd><cEAN>SEM GTIN</cEAN><xProd>{x_prod}</xProd><NCM>{item.ncm or "21069029"}</NCM><CFOP>5102</CFOP><uCom>{item.produto.unidade}</uCom><qCom>{item.quantidade:.4f}</qCom><vUnCom>{item.preco_unitario:.4f}</vUnCom><vProd>{item.subtotal:.2f}</vProd><cEANTrib>SEM GTIN</cEANTrib><uTrib>{item.produto.unidade}</uTrib><qTrib>{item.quantidade:.4f}</qTrib><vUnTrib>{item.preco_unitario:.4f}</vUnTrib><indTot>1</indTot></prod><imposto><ICMS><ICMSSN102><orig>{item.origem or 0}</orig><CSOSN>102</CSOSN></ICMSSN102></ICMS><PIS><PISNT><CST>07</CST></PISNT></PIS><COFINS><COFINSNT><CST>07</CST></COFINSNT></COFINS></imposto></det>'
        
        xml += f'<total><ICMSTot><vBC>0.00</vBC><vICMS>0.00</vICMS><vICMSDeson>0.00</vICMSDeson><vFCP>0.00</vFCP><vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet><vProd>{venda.total:.2f}</vProd><vFrete>0.00</vFrete><vSeg>0.00</vSeg><vDesc>0.00</vDesc><vII>0.00</vII><vIPI>0.00</vIPI><vIPIDevol>0.00</vIPIDevol><vPIS>0.00</vPIS><vCOFINS>0.00</vCOFINS><vOutro>0.00</vOutro><vNF>{venda.total:.2f}</vNF></ICMSTot></total>'
        xml += '<transp><modFrete>9</modFrete></transp>'
        xml += f'<pag><detPag><tPag>01</tPag><vPag>{venda.total:.2f}</vPag></detPag></pag></infNFe><infNFeSupl><qrCode>{qr}</qrCode><urlChave>{url.replace("qrcode", "consulta")}</urlChave></infNFeSupl></NFe>'
        return xml

    @staticmethod
    def emitir_nfce(db: Session, venda: Venda):
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
        if not nota: nota = NotaFiscalModel(venda_id=venda.id, status_sefaz="PENDENTE", motivo_sefaz="Iniciando"); db.add(nota); db.commit(); db.refresh(nota)
        logs = f"[{datetime.now().isoformat()}] INICIO: Emissão Venda {venda.id}\n"
        
        # BUSCA EMPRESA E FORÇA REFRESH PARA PEGAR O NÚMERO MAIS ATUAL
        empresa = db.query(Empresa).first()
        db.refresh(empresa)
        
        try:
            # Pega o próximo número fiscal
            numero_nf = (empresa.ultimo_numero_nf or 0) + 1
            print(f">>> [FISCAL] EMITINDO NOTA FISCAL Nº: {numero_nf} (Venda {venda.id})")
            
            cert_path = empresa.certificado_path
            if not os.path.exists(cert_path): cert_path = os.path.join("storage/certs", os.path.basename(empresa.certificado_path))
            with open(cert_path, "rb") as f: pfx_data = f.read()
            pw = (empresa.certificado_senha or "").strip().encode()
            
            # Chave base agora usa o numero_nf oficial
            chave_base = f"35{datetime.now().strftime('%y%m')}{empresa.cnpj.zfill(14)}65001{str(numero_nf).zfill(9)}1{str(numero_nf).zfill(8)}"
            dv = SefazService.calcular_dv(chave_base); chave = chave_base + str(dv)
            
            xml_puro = SefazService._gerar_xml_limpo(empresa, venda, chave, numero_nf)
            
            from erpbrasil.assinatura.assinatura import XMLSignerWithSHA1
            import signxml
            p12 = pkcs12.load_key_and_certificates(pfx_data, pw, default_backend())
            pkey, pcert, others = (p12[0], p12[1], p12[2]) if isinstance(p12, tuple) else (p12.key, p12.cert, p12.othercerts)
            
            class Cert:
                def __init__(self, k, c, o, p):
                    self.key, self.cert, self.othercerts, self._senha = k, c, o, p
                    self._chave = k.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
                    cpem = c.public_bytes(Encoding.PEM)
                    for ot in o: cpem += ot.public_bytes(Encoding.PEM)
                    self._cert = cpem
                def cert_chave(self): return self._cert.decode(), self._chave.decode()
            cert_obj = Cert(pkey, pcert, others, pw)
            
            root = etree.fromstring(xml_puro.encode('utf-8'))
            signer = XMLSignerWithSHA1(method=signxml.methods.enveloped, signature_algorithm="rsa-sha1", digest_algorithm="sha1", c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
            signer.namespaces = {None: signxml.namespaces.ds}
            signed_root = signer.sign(root, key=pkey, cert=pcert.public_bytes(Encoding.PEM), reference_uri=f"#NFe{chave}")
            
            xml_assinado = etree.tostring(signed_root, encoding='unicode')
            xml_assinado = xml_assinado.replace(' xmlns="http://www.portalfiscal.inf.br/nfe"', '').replace('<NFe', '<NFe xmlns="http://www.portalfiscal.inf.br/nfe"', 1)
            xml_assinado = re.sub(r'<\?xml.*?\?>', '', xml_assinado).strip()

            url_s = "https://homologacao.nfce.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx" if empresa.ambiente == 2 else "https://nfce.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx"
            id_lote = str(venda.id).zfill(1)
            lote_xml = f'<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><idLote>{id_lote}</idLote><indSinc>1</indSinc>{xml_assinado}</enviNFe>'
            env = f'<?xml version="1.0" encoding="utf-8"?><soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">{lote_xml}</nfeDadosMsg></soap12:Body></soap12:Envelope>'
            
            ct, kt = tempfile.NamedTemporaryFile(delete=False), tempfile.NamedTemporaryFile(delete=False)
            try:
                cert_pem = pcert.public_bytes(Encoding.PEM)
                for ot in others: cert_pem += ot.public_bytes(Encoding.PEM)
                ct.write(cert_pem); ct.close(); kt.write(pkey.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())); kt.close()
                res = requests.post(url=url_s, data=env.encode('utf-8'), headers={"Content-Type": "application/soap+xml; charset=utf-8"}, cert=(ct.name, kt.name), verify=False, timeout=30)
                
                nota.xml_enviado, nota.xml_recebido = xml_assinado, res.text
                # 5. Processamento do Retorno (Aceita 100-Sucesso, 102-Lote, 204-Duplicidade)
                xml_res = res.text
                if any(x in xml_res for x in ["<cStat>100</cStat>", "<cStat>102</cStat>", "<cStat>204</cStat>"]):
                    nota.status_sefaz, nota.motivo_sefaz = "100", "Autorizado"
                    
                    # Busca o protocolo em qualquer lugar da resposta (normal ou erro de duplicidade)
                    n_prot = re.search(r"<nProt>(.*?)</nProt>", xml_res)
                    ch_nfe = re.search(r"<chNFe>(.*?)</chNFe>", xml_res)
                    
                    if n_prot: nota.protocolo = n_prot.group(1)
                    if ch_nfe: nota.chave_acesso = ch_nfe.group(1)
                    nota.numero_nota = numero_nf
                    
                    # Incrementa o sequenciador se for uma nota nova
                    if "<cStat>204</cStat>" not in xml_res:
                        empresa.ultimo_numero_nf = numero_nf
                        db.add(empresa)
                    
                    # Tenta montar o xml_autorizado completo
                    pm = re.search(r"<protNFe.*?>(.*?)</protNFe>", xml_res, re.DOTALL)
                    if pm:
                        px = pm.group(0)
                        nota.xml_autorizado = f'<?xml version="1.0" encoding="utf-8"?><nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">{xml_assinado}{px}</nfeProc>'
                    
                    venda.status = "PAGA"
                    db.add(venda)
                else:
                    m = re.search(r"<xMotivo>(.*?)</xMotivo>", res.text)
                    nota.status_sefaz, nota.motivo_sefaz = "ERRO", m.group(1) if m else "Rejeição"

            finally:
                [os.remove(x) for x in [ct.name, kt.name] if os.path.exists(x)]
            nota.logs_transmissao = logs; db.commit(); return nota
        except Exception as e:
            db.rollback(); nota_u = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
            if nota_u: nota_u.status_sefaz, nota_u.motivo_sefaz, nota_u.logs_transmissao = "ERRO", str(e), logs + str(e); db.commit()
            raise e
    @staticmethod
    def gerar_danfe_pdf(db: Session, venda_id: int, largura: int = 80) -> io.BytesIO:
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        venda = db.query(Venda).filter(Venda.id == venda_id).first()
        empresa = db.query(Empresa).first()

        if not nota or not nota.xml_autorizado:
            raise Exception("Nota não autorizada ou XML não encontrado.")

        # Conversão de mm para pontos (pt)
        # 80mm ~ 226pt, 58mm ~ 164pt
        width_pt = 226 if largura == 80 else 164
        center_x = width_pt / 2
        right_margin = width_pt - 10

        try:
            # Tenta o gerador oficial (Layout completo da NFC-e)
            from erpbrasil.edoc.pdf import danfe
            # O gerador oficial geralmente é fixo em A4 ou 80mm, mantemos como está
            return io.BytesIO(danfe.Danfe(xml=nota.xml_autorizado.encode('utf-8'), logo='').output())
        except Exception:
            # Fallback PROFISSIONAL e FLEXÍVEL
            from reportlab.graphics.barcode.qr import QrCodeWidget
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics import renderPDF

            buffer = io.BytesIO()
            # Altura dinâmica baseada na qtd de itens (simplificado)
            height_pt = 450 + (len(venda.itens) * 25)
            c = canvas.Canvas(buffer, pagesize=(width_pt, height_pt)) 
            y = height_pt - 20 # Início do topo

            # 1. EMITENTE
            c.setFont("Helvetica-Bold", 10 if largura == 80 else 9)
            c.drawCentredString(center_x, y, empresa.razao_social[:35])
            y -= 12
            c.setFont("Helvetica", 8)
            c.drawCentredString(center_x, y, f"CNPJ: {empresa.cnpj}")
            y -= 10
            c.drawCentredString(center_x, y, f"{empresa.municipio_nome or 'CIDADE'} - {empresa.uf or 'SP'}")
            y -= 15

            c.line(10, y, right_margin, y)
            y -= 15

            # 2. IDENTIFICAÇÃO DANFE
            c.setFont("Helvetica-Bold", 9 if largura == 80 else 8)
            c.drawCentredString(center_x, y, "DANFE NFC-e - Documento Auxiliar")
            y -= 10
            c.drawCentredString(center_x, y, "da Nota Fiscal de Consumidor Eletrônica")
            y -= 15

            # 3. ITENS (Layout em duas linhas para maior clareza)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(10, y, "CÓD   DESCRIÇÃO")
            y -= 10
            c.drawString(10, y, "      QTD x UNIT                         TOTAL")
            y -= 12
            
            c.line(10, y+2, right_margin, y+2)
            
            c.setFont("Helvetica", 8)
            for i, item in enumerate(venda.itens):
                # Linha 1: Índice e Descrição
                desc = item.produto.descricao[:25]
                c.setFont("Helvetica-Bold", 8)
                c.drawString(10, y, f"{str(i+1).zfill(3)}  {desc}")
                y -= 10
                
                # Linha 2: Detalhes do preço e total
                c.setFont("Helvetica", 8)
                detalhe = f"      {item.quantidade:.2f} {item.produto.unidade} x {item.preco_unitario:.2f}"
                c.drawString(10, y, detalhe)
                c.drawRightString(right_margin, y, f"{item.subtotal:.2f}")
                y -= 12
                
                if y < 160: break # Limite de segurança

            y -= 5
            c.line(10, y, right_margin, y)
            y -= 15

            # 4. TOTAIS E PAGAMENTO
            c.setFont("Helvetica-Bold", 10)
            c.drawString(10, y, "VALOR TOTAL R$")
            c.drawRightString(right_margin, y, f"{venda.total:.2f}")
            y -= 15
            c.setFont("Helvetica", 9)
            forma = venda.forma_pagamento or "DINHEIRO"
            c.drawString(10, y, f"PAGAMENTO: {forma}")
            y -= 25

            # 5. AUTORIZAÇÃO
            c.setFont("Helvetica-Bold", 8 if largura == 80 else 7)
            c.drawCentredString(center_x, y, "Consulte pela Chave de Acesso em:")
            y -= 10
            c.setFont("Helvetica", 7)
            c.drawCentredString(center_x, y, "www.nfce.fazenda.sp.gov.br/consulta")
            y -= 12

            # Chave de Acesso
            chave = nota.chave_acesso
            if chave:
                chave_fmt = " ".join([chave[i:i+4] for i in range(0, len(chave), 4)])
                c.setFont("Helvetica-Bold", 7)
                # Se 58mm, quebra a chave em duas linhas
                if largura == 58:
                    c.drawCentredString(center_x, y, chave_fmt[:27])
                    y -= 9
                    c.drawCentredString(center_x, y, chave_fmt[27:])
                else:
                    c.drawCentredString(center_x, y, chave_fmt)
                y -= 15

            c.setFont("Helvetica", 8)
            c.drawCentredString(center_x, y, f"Protocolo: {nota.protocolo or ''}")
            y -= 10
            c.drawCentredString(center_x, y, "Autorizado o uso da NF-e")
            y -= 10
            
            # 6. QR CODE (Centralizado conforme a largura)
            chave = nota.chave_acesso
            url_base = "https://www.nfce.fazenda.sp.gov.br/qrcode" if empresa.ambiente == 1 else "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode"
            id_token = str(int(empresa.csc_id or 1))
            p_param = f"{chave}|2|{empresa.ambiente}|{id_token}"
            cHash = hashlib.sha1((p_param + (empresa.csc_token or "")).encode()).hexdigest().upper()
            qr_url = f"{url_base}?p={p_param}|{cHash}"
            
            qr_code = QrCodeWidget(qr_url)
            d = Drawing(100, 100)
            d.add(qr_code)
            # Desenha o QR Code (centralizado: centro - 50pt)
            renderPDF.draw(d, c, center_x - 50, y - 110)
            
            c.save()
            buffer.seek(0)
            return buffer
