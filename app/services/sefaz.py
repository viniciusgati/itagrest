import os, io, binascii, re, hashlib, tempfile, requests
os.environ["OPENSSL_CONF"] = "/app/openssl_legacy.cnf"
from lxml import etree
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from app.models.venda import Venda, VendaItem
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
        import html
        def escape(t): return html.escape(str(t or "")).strip()

        dh_obj = datetime.now(timezone(timedelta(hours=-3)))
        dh = dh_obj.strftime('%Y-%m-%dT%H:%M:%S-03:00')
        ibge = empresa.municipio_ibge or "3550308"
        url = "https://www.nfce.fazenda.sp.gov.br/qrcode" if empresa.ambiente == 1 else "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode"
        
        # QR Code SP v2.00 (Rigoroso)
        id_token = str(int(empresa.csc_id or 1))
        p = f"{chave}|2|{empresa.ambiente}|{id_token}"
        cHash = hashlib.sha1((p + (empresa.csc_token or "")).encode()).hexdigest().upper()
        qr = f"{url}?p={p}|{cHash}"
        
        xml = f'<NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe versao="4.00" Id="NFe{chave}">'
        xml += f'<ide><cUF>35</cUF><cNF>{str(numero_nf).zfill(8)}</cNF><natOp>VENDA</natOp><mod>65</mod><serie>1</serie><nNF>{numero_nf}</nNF><dhEmi>{dh}</dhEmi><tpNF>1</tpNF><idDest>1</idDest><cMunFG>{ibge}</cMunFG><tpImp>4</tpImp><tpEmis>1</tpEmis><cDV>{chave[-1]}</cDV><tpAmb>{empresa.ambiente}</tpAmb><finNFe>1</finNFe><indFinal>1</indFinal><indPres>1</indPres><procEmi>0</procEmi><verProc>1.0.0</verProc></ide>'
        xml += f'<emit><CNPJ>{empresa.cnpj}</CNPJ><xNome>{escape(empresa.razao_social)}</xNome><enderEmit><xLgr>{escape(empresa.logradouro or "RUA")}</xLgr><nro>{escape(empresa.numero or "SN")}</nro><xBairro>{escape(empresa.bairro or "BAIRRO")}</xBairro><cMun>{ibge}</cMun><xMun>{escape(empresa.municipio_nome or "CIDADE")}</xMun><UF>{empresa.uf or "SP"}</UF><CEP>{empresa.cep or "01000000"}</CEP><cPais>1058</cPais><xPais>BRASIL</xPais></enderEmit><IE>{empresa.inscricao_estadual}</IE><CRT>1</CRT></emit>'
        
        if venda.cliente:
            tag = "CNPJ" if len(venda.cliente.documento) > 11 else "CPF"
            xml += f'<dest><{tag}>{venda.cliente.documento}</{tag}><xNome>{escape(venda.cliente.nome[:60])}</xNome><indIEDest>9</indIEDest></dest>'
        
        # Recalcula total real dos itens para o XML
        total_xml = 0
        for i, item in enumerate(venda.itens):
            x_prod = item.produto.descricao
            if i == 0 and empresa.ambiente == 2:
                x_prod = "NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
            subtotal = float(item.subtotal)
            total_xml += subtotal
            xml += f'<det nItem="{i+1}"><prod><cProd>{item.id}</cProd><cEAN>SEM GTIN</cEAN><xProd>{escape(x_prod)}</xProd><NCM>{item.ncm or "21069029"}</NCM><CFOP>5102</CFOP><uCom>{item.produto.unidade}</uCom><qCom>{item.quantidade:.4f}</qCom><vUnCom>{item.preco_unitario:.4f}</vUnCom><vProd>{subtotal:.2f}</vProd><cEANTrib>SEM GTIN</cEANTrib><uTrib>{item.produto.unidade}</uTrib><qTrib>{item.quantidade:.4f}</qTrib><vUnTrib>{item.preco_unitario:.4f}</vUnTrib><indTot>1</indTot></prod><imposto><ICMS><ICMSSN102><orig>{item.origem or 0}</orig><CSOSN>102</CSOSN></ICMSSN102></ICMS><PIS><PISNT><CST>07</CST></PISNT></PIS><COFINS><COFINSNT><CST>07</CST></COFINSNT></COFINS></imposto></det>'
        
        xml += f'<total><ICMSTot><vBC>0.00</vBC><vICMS>0.00</vICMS><vICMSDeson>0.00</vICMSDeson><vFCP>0.00</vFCP><vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet><vProd>{total_xml:.2f}</vProd><vFrete>0.00</vFrete><vSeg>0.00</vSeg><vDesc>0.00</vDesc><vII>0.00</vII><vIPI>0.00</vIPI><vIPIDevol>0.00</vIPIDevol><vPIS>0.00</vPIS><vCOFINS>0.00</vCOFINS><vOutro>0.00</vOutro><vNF>{total_xml:.2f}</vNF></ICMSTot></total>'
        xml += '<transp><modFrete>9</modFrete></transp>'
        
        # 4. PAGAMENTO
        tpag_map = {"DINHEIRO": "01", "CARTAO_CREDITO": "99", "CARTAO_DEBITO": "99", "PIX": "17"}
        tpag = tpag_map.get(venda.forma_pagamento.value if venda.forma_pagamento else "", "01")
        xml += f'<pag><detPag><tPag>{tpag}</tPag><vPag>{total_xml:.2f}</vPag></detPag></pag>'

        # 5. INFORMAÇÕES ADICIONAIS (Sanitizado Profissionalmente)
        if empresa.observacoes_nf:
            obs_esc = escape(empresa.observacoes_nf.replace('\n', ' ').replace('\r', ' '))
            xml += f'<infAdic><infCpl>{obs_esc[:500]}</infCpl></infAdic>'
        
        xml += f'</infNFe><infNFeSupl><qrCode>{escape(qr)}</qrCode><urlChave>{escape(url.replace("qrcode", "consulta"))}</urlChave></infNFeSupl></NFe>'
        return xml

    @staticmethod
    def emitir_nfce(db: Session, venda: Venda):
        # 0. RECARREGA A VENDA COM ITENS E PRODUTOS (EAGER LOADING)
        venda = db.query(Venda).options(
            joinedload(Venda.itens).joinedload(VendaItem.produto)
        ).filter(Venda.id == venda.id).first()

        # SUPER TRAVA FISCAL: Bloqueia emissão se não houver valor ou itens reais
        if not venda.itens or len(venda.itens) == 0:
            raise Exception(f"BLOQUEIO FISCAL: A Venda #{venda.id} não possui produtos. Adicione itens antes de emitir.")
        
        total_calculado = sum(float(item.subtotal) for item in venda.itens)
        if total_calculado <= 0:
            raise Exception(f"BLOQUEIO FISCAL: O valor total da Venda #{venda.id} é R$ {total_calculado:.2f}. Não é permitido emitir nota zerada.")
        
        if float(venda.total) <= 0:
            # Se o total do banco estiver errado mas os itens estiverem certos, corrigimos o total
            venda.total = total_calculado
            db.add(venda)
            db.commit()
            db.refresh(venda)

        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda.id).first()
        if not nota:
            nota = NotaFiscalModel(venda_id=venda.id, status_sefaz="PENDENTE", motivo_sefaz="Iniciando")
            db.add(nota); db.commit(); db.refresh(nota)
        
        logs = f"[{datetime.now().isoformat()}] INICIO: Emissão Venda {venda.id}\n"
        empresa = db.query(Empresa).first()
        db.refresh(empresa)
        
        try:
            numero_nf = (empresa.ultimo_numero_nf or 0) + 1
            dh_ref = datetime.now(timezone(timedelta(hours=-3)))
            chave_base = f"35{dh_ref.strftime('%y%m')}{empresa.cnpj.zfill(14)}65001{str(numero_nf).zfill(9)}1{str(numero_nf).zfill(8)}"
            dv = SefazService.calcular_dv(chave_base); chave = chave_base + str(dv)
            
            with open(os.path.join("storage/certs", os.path.basename(empresa.certificado_path)), "rb") as f: pfx_data = f.read()
            pw = (empresa.certificado_senha or "").strip().encode('utf-8')
            
            xml_puro = SefazService._gerar_xml_limpo(empresa, venda, chave, numero_nf)
            
            from erpbrasil.assinatura.assinatura import XMLSignerWithSHA1
            import signxml
            p12 = pkcs12.load_key_and_certificates(pfx_data, pw, default_backend())
            pkey, pcert, others = (p12[0], p12[1], p12[2]) if isinstance(p12, tuple) else (p12.key, p12.cert, p12.othercerts)
            
            root = etree.fromstring(xml_puro.encode('utf-8'))
            signer = XMLSignerWithSHA1(method=signxml.methods.enveloped, signature_algorithm="rsa-sha1", digest_algorithm="sha1", c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
            signer.namespaces = {None: signxml.namespaces.ds}
            signed_root = signer.sign(root, key=pkey, cert=pcert.public_bytes(Encoding.PEM), reference_uri=f"#NFe{chave}")
            
            xml_assinado = etree.tostring(signed_root, encoding='unicode')
            xml_assinado = xml_assinado.replace(' xmlns="http://www.portalfiscal.inf.br/nfe"', '').replace('<NFe', '<NFe xmlns="http://www.portalfiscal.inf.br/nfe"', 1)
            xml_assinado = re.sub(r'<\?xml.*?\?>', '', xml_assinado).strip()

            url_s = "https://nfce.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx" if empresa.ambiente == 1 else "https://homologacao.nfce.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx"
            lote_xml = f'<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><idLote>{venda.id}</idLote><indSinc>1</indSinc>{xml_assinado}</enviNFe>'
            env = f'<?xml version="1.0" encoding="utf-8"?><soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">{lote_xml}</nfeDadosMsg></soap12:Body></soap12:Envelope>'
            
            ct, kt = tempfile.NamedTemporaryFile(delete=False), tempfile.NamedTemporaryFile(delete=False)
            try:
                cert_pem = pcert.public_bytes(Encoding.PEM)
                for ot in others: cert_pem += ot.public_bytes(Encoding.PEM)
                ct.write(cert_pem); ct.close(); kt.write(pkey.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())); kt.close()
                res = requests.post(url=url_s, data=env.encode('utf-8'), headers={"Content-Type": "application/soap+xml; charset=utf-8"}, cert=(ct.name, kt.name), verify=False, timeout=30)
                
                nota.xml_enviado, nota.xml_recebido = xml_assinado, res.text
                if any(x in res.text for x in ["<cStat>100</cStat>", "<cStat>102</cStat>", "<cStat>204</cStat>"]):
                    nota.status_sefaz, nota.motivo_sefaz = "100", "Autorizado"
                    n_prot = re.search(r"<nProt>(.*?)</nProt>", res.text)
                    ch_nfe = re.search(r"<chNFe>(.*?)</chNFe>", res.text)
                    if n_prot: nota.protocolo = n_prot.group(1)
                    if ch_nfe: nota.chave_acesso = ch_nfe.group(1)
                    nota.numero_nota = numero_nf
                    if "<cStat>204</cStat>" not in res.text:
                        empresa.ultimo_numero_nf = numero_nf
                        db.add(empresa)
                    pm = re.search(r"<protNFe.*?>(.*?)</protNFe>", res.text, re.DOTALL)
                    if pm: nota.xml_autorizado = f'<?xml version="1.0" encoding="utf-8"?><nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">{xml_assinado}{pm.group(0)}</nfeProc>'
                    venda.status = "PAGA"; db.add(venda)
                else:
                    m = re.search(r"<xMotivo>(.*?)</xMotivo>", res.text)
                    nota.status_sefaz, nota.motivo_sefaz = "ERRO", m.group(1) if m else "Rejeição"
            finally:
                [os.remove(x) for x in [ct.name, kt.name] if os.path.exists(x)]
            db.commit(); return nota
        except Exception as e:
            db.rollback(); raise e

    @staticmethod
    def cancelar_nfce(db: Session, venda_id: int, justificativa: str):
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        if not nota:
            raise Exception("Nenhuma nota fiscal encontrada para esta venda.")
        if nota.status_sefaz != "100":
            raise Exception("A nota não está autorizada. Apenas notas com status '100' (Autorizado) podem ser canceladas.")
        if nota.protocolo_cancelamento:
            raise Exception("Esta nota já foi cancelada.")

        justificativa = justificativa.strip()
        if len(justificativa) < 15:
            raise Exception("Justificativa deve ter no mínimo 15 caracteres.")

        empresa = db.query(Empresa).first()
        db.refresh(empresa)

        chave = nota.chave_acesso
        protocolo = nota.protocolo
        tp_evento = "110111"
        seq = "01"
        id_evento = f"ID{tp_evento}{chave}{seq}"

        dh_ref = datetime.now(timezone(timedelta(hours=-3)))
        dh_evento = dh_ref.strftime('%Y-%m-%dT%H:%M:%S-03:00')

        # 1. Monta XML do evento (sem assinatura)
        evento_xml = (
            f'<evento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">'
            f'<infEvento Id="{id_evento}">'
            f'<cOrgao>35</cOrgao>'
            f'<tpAmb>{empresa.ambiente}</tpAmb>'
            f'<CNPJ>{empresa.cnpj}</CNPJ>'
            f'<chNFe>{chave}</chNFe>'
            f'<dhEvento>{dh_evento}</dhEvento>'
            f'<tpEvento>{tp_evento}</tpEvento>'
            f'<nSeqEvento>1</nSeqEvento>'
            f'<verEvento>1.00</verEvento>'
            f'<detEvento versao="1.00">'
            f'<descEvento>Cancelamento</descEvento>'
            f'<nProt>{protocolo}</nProt>'
            f'<xJust>{justificativa}</xJust>'
            f'</detEvento>'
            f'</infEvento>'
            f'</evento>'
        )

        with open(os.path.join("storage/certs", os.path.basename(empresa.certificado_path)), "rb") as f:
            pfx_data = f.read()
        pw = (empresa.certificado_senha or "").strip().encode('utf-8')

        from erpbrasil.assinatura.assinatura import XMLSignerWithSHA1
        import signxml
        p12 = pkcs12.load_key_and_certificates(pfx_data, pw, default_backend())
        pkey, pcert, others = (p12[0], p12[1], p12[2]) if isinstance(p12, tuple) else (p12.key, p12.cert, p12.othercerts)

        root = etree.fromstring(evento_xml.encode('utf-8'))
        signer = XMLSignerWithSHA1(method=signxml.methods.enveloped, signature_algorithm="rsa-sha1", digest_algorithm="sha1", c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
        signer.namespaces = {None: signxml.namespaces.ds}
        signed_root = signer.sign(root, key=pkey, cert=pcert.public_bytes(Encoding.PEM), reference_uri=f"#{id_evento}")

        xml_assinado = etree.tostring(signed_root, encoding='unicode')
        xml_assinado = xml_assinado.replace(' xmlns="http://www.portalfiscal.inf.br/nfe"', '').replace('<evento', '<evento xmlns="http://www.portalfiscal.inf.br/nfe"', 1)
        xml_assinado = re.sub(r'<\?xml.*?\?>', '', xml_assinado).strip()

        # 2. Envelopa em envEvento + SOAP
        url_s = "https://nfce.fazenda.sp.gov.br/ws/NFeRecepcaoEvento4.asmx" if empresa.ambiente == 1 else "https://homologacao.nfce.fazenda.sp.gov.br/ws/NFeRecepcaoEvento4.asmx"
        lote_id = f"{venda_id}{int(dh_ref.timestamp())}"[-15:]
        env_evento = f'<envEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>{lote_id}</idLote>{xml_assinado}</envEvento>'
        env = (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">'
            f'<soap12:Body>'
            f'<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4">{env_evento}</nfeDadosMsg>'
            f'</soap12:Body>'
            f'</soap12:Envelope>'
        )

        ct, kt = tempfile.NamedTemporaryFile(delete=False), tempfile.NamedTemporaryFile(delete=False)
        try:
            cert_pem = pcert.public_bytes(Encoding.PEM)
            for ot in others:
                cert_pem += ot.public_bytes(Encoding.PEM)
            ct.write(cert_pem); ct.close()
            kt.write(pkey.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())); kt.close()
            res = requests.post(url=url_s, data=env.encode('utf-8'), headers={"Content-Type": "application/soap+xml; charset=utf-8"}, cert=(ct.name, kt.name), verify=False, timeout=30)

            nota.xml_recebido = nota.xml_recebido + "\n\n--- CANCELAMENTO ---\n" + res.text if nota.xml_recebido else res.text

            if "<cStat>135</cStat>" in res.text:
                n_prot = re.search(r"<nProt>(.*?)</nProt>", res.text)
                nota.protocolo_cancelamento = n_prot.group(1) if n_prot else "SEM_PROTOCOLO"
                nota.motivo_cancelamento = "Cancelamento homologado"
                nota.data_cancelamento = dh_ref
                nota.status_sefaz = "CANCELADA"
                db.commit()
            else:
                m = re.search(r"<xMotivo>(.*?)</xMotivo>", res.text)
                nota.status_sefaz = "ERRO"
                nota.motivo_sefaz = (m.group(1) if m else "Erro no cancelamento") + " (cancelamento)"
                db.commit()
                raise Exception(nota.motivo_sefaz)
        finally:
            for x in [ct.name, kt.name]:
                if os.path.exists(x):
                    os.remove(x)
        return nota

    @staticmethod
    def gerar_danfe_pdf(db: Session, venda_id: int, largura: int = 80) -> io.BytesIO:
        from reportlab.pdfgen import canvas
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        venda = db.query(Venda).filter(Venda.id == venda_id).first()
        empresa = db.query(Empresa).first()
        if not nota or not nota.xml_autorizado: raise Exception("Nota não autorizada.")
        
        width_pt = 226 if largura == 80 else 164
        center_x = width_pt / 2
        right_margin = width_pt - 10
        
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPDF
        buffer = io.BytesIO()
        height_pt = 600 + (len(venda.itens) * 35)
        c = canvas.Canvas(buffer, pagesize=(width_pt, height_pt)); y = height_pt - 20
        
        c.setFont("Helvetica-Bold", 10 if largura == 80 else 9)
        c.drawCentredString(center_x, y, (empresa.nome_fantasia or empresa.razao_social)[:35].upper()); y -= 12
        c.setFont("Helvetica", 8); c.drawCentredString(center_x, y, f"CNPJ: {empresa.cnpj}"); y -= 10
        c.drawCentredString(center_x, y, f"{empresa.municipio_nome or 'CIDADE'} - {empresa.uf or 'SP'}"); y -= 15
        c.line(10, y, right_margin, y); y -= 15
        
        c.setFont("Helvetica-Bold", 8)
        if venda.cliente:
            c.drawCentredString(center_x, y, "CONSUMIDOR"); y -= 10
            c.setFont("Helvetica", 8); c.drawCentredString(center_x, y, f"{venda.cliente.nome[:35]}"); y -= 10
            c.drawCentredString(center_x, y, f"CNPJ/CPF: {venda.cliente.documento}")
        else: c.drawCentredString(center_x, y, "CONSUMIDOR NÃO IDENTIFICADO")
        y -= 15; c.line(10, y, right_margin, y); y -= 15
        
        c.setFont("Helvetica-Bold", 8); c.drawString(10, y, "CÓD   DESCRIÇÃO"); y -= 10
        c.drawString(10, y, "      QTD x UNIT                         TOTAL"); y -= 12
        for i, item in enumerate(venda.itens):
            c.setFont("Helvetica-Bold", 8); c.drawString(10, y, f"{str(i+1).zfill(3)}  {item.produto.descricao[:25]}"); y -= 10
            c.setFont("Helvetica", 8); c.drawString(10, y, f"      {item.quantidade:.2f} {item.produto.unidade} x {item.preco_unitario:.2f}")
            c.drawRightString(right_margin, y, f"{item.subtotal:.2f}"); y -= 12
        y -= 5; c.line(10, y, right_margin, y); y -= 15
        
        c.setFont("Helvetica-Bold", 10); c.drawString(10, y, "VALOR TOTAL R$"); c.drawRightString(right_margin, y, f"{venda.total:.2f}"); y -= 15
        c.setFont("Helvetica", 9); c.drawString(10, y, f"PAGAMENTO: {venda.forma_pagamento or 'DINHEIRO'}"); y -= 20
        
        # OBSERVAÇÕES (Apenas na Impressão)
        if empresa.observacoes_nf:
            c.setFont("Helvetica-Bold", 8); c.drawString(10, y, "INFORMAÇÕES COMPLEMENTARES"); y -= 10
            c.setFont("Helvetica", 7); max_c = 45 if largura == 80 else 35
            for lin in empresa.observacoes_nf.replace('\r','').split('\n'):
                for i in range(0, len(lin), max_c): c.drawString(15, y, lin[i:i+max_c]); y -= 8
            y -= 10
        
        c.setFont("Helvetica-Bold", 8); c.drawCentredString(center_x, y, "Consulte pela Chave de Acesso em:"); y -= 10
        c.setFont("Helvetica", 7); c.drawCentredString(center_x, y, "www.nfce.fazenda.sp.gov.br/consulta"); y -= 12
        
        # Busca Chave e Protocolo do XML se necessário
        chave = nota.chave_acesso
        if not chave:
            try:
                root = etree.fromstring(nota.xml_autorizado.encode('utf-8'))
                inf = root.find(".//{http://www.portalfiscal.inf.br/nfe}infNFe")
                if inf is not None: chave = inf.get("Id", "")[3:]
            except: pass
            
        if chave:
            ch_f = " ".join([chave[i:i+4] for i in range(0, len(chave), 4)])
            c.setFont("Helvetica-Bold", 7)
            if largura == 58:
                c.drawCentredString(center_x, y, ch_f[:27]); y -= 9; c.drawCentredString(center_x, y, ch_f[27:])
            else: c.drawCentredString(center_x, y, ch_f)
            y -= 15; c.setFont("Helvetica", 8); c.drawCentredString(center_x, y, f"Protocolo: {nota.protocolo or ''}"); y -= 10
            c.drawCentredString(center_x, y, "Autorizado o uso da NF-e"); y -= 10
            url_b = "https://www.nfce.fazenda.sp.gov.br/qrcode" if empresa.ambiente == 1 else "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode"
            p_p = f"{chave}|2|{empresa.ambiente}|{str(int(empresa.csc_id or 1))}"
            cHs = hashlib.sha1((p_p + (empresa.csc_token or "")).encode()).hexdigest().upper()
            qr_code = QrCodeWidget(f"{url_b}?p={p_p}|{cHs}"); d = Drawing(100, 100); d.add(qr_code); renderPDF.draw(d, c, center_x - 50, y - 110)
        
        c.save(); buffer.seek(0); return buffer

    @staticmethod
    def gerar_danfe_a4(db: Session, venda_id: int) -> io.BytesIO:
        """
        Gera a DANFE completa em formato A4 (PDF) usando a biblioteca brazilfiscalreport.
        Ideal para impressoras laser/jato de tinta.
        """
        from brazilfiscalreport.danfe import Danfe
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        if not nota or not nota.xml_autorizado: 
            raise Exception("Nota não autorizada para esta venda ou XML de autorização ausente.")
        
        try:
            # O XML autorizado deve conter a tag nfeProc (NFe + Protocolo)
            xml_content = nota.xml_autorizado.encode('utf-8')
            danfe = Danfe(xml_content)
            pdf_bytes = danfe.output()
            return io.BytesIO(pdf_bytes)
        except Exception as e:
            raise Exception(f"Erro ao gerar DANFE A4: {str(e)}")
