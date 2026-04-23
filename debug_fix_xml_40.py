import os, io, re, hashlib, requests, tempfile
from datetime import datetime, timezone, timedelta
os.environ["OPENSSL_CONF"] = "/app/openssl_legacy.cnf"
from lxml import etree
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.venda import Venda
from app.models.nota_fiscal import NotaFiscal as NotaFiscalModel
from app.models.empresa import Empresa
from app.services.sefaz import SefazService
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend

def fix_and_emit_43():
    db = SessionLocal()
    venda_id = 43
    print(f"--- INICIANDO FIX MANUAL VENDA {venda_id} ---")
    
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    empresa = db.query(Empresa).first()
    nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
    
    # Próximo número disponível
    numero_nf = (empresa.ultimo_numero_nf or 0) + 1
    chave_base = f"352604{empresa.cnpj.zfill(14)}65001{str(numero_nf).zfill(9)}1{str(numero_nf).zfill(8)}"
    dv = SefazService.calcular_dv(chave_base)
    chave = chave_base + str(dv)
    
    print(f"Tentando emitir Nota {numero_nf} para Venda {venda_id}...")
    
    # 1. Geração do XML com ORDEM CORRETA
    xml_puro = SefazService._gerar_xml_limpo(empresa, venda, chave, numero_nf)
    from datetime import timezone, timedelta
    dh_obj = datetime.now(timezone(timedelta(hours=-3)))
    dh = dh_obj.strftime('%Y-%m-%dT%H:%M:%S-03:00')
    ibge = empresa.municipio_ibge or "3550308"
    url = "https://www.nfce.fazenda.sp.gov.br/qrcode" if empresa.ambiente == 1 else "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode"
    id_token = str(int(empresa.csc_id or 1))
    p = f"{chave}|2|{empresa.ambiente}|{id_token}"
    cHash = hashlib.sha1((p + (empresa.csc_token or "")).encode()).hexdigest().upper()
    qr = f"{url}?p={p}|{cHash}"
    
    xml_puro = f'<NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe versao="4.00" Id="NFe{chave}">'
    xml_puro += f'<ide><cUF>35</cUF><cNF>{str(numero_nf).zfill(8)}</cNF><natOp>VENDA</natOp><mod>65</mod><serie>1</serie><nNF>{numero_nf}</nNF><dhEmi>{dh}</dhEmi><tpNF>1</tpNF><idDest>1</idDest><cMunFG>{ibge}</cMunFG><tpImp>4</tpImp><tpEmis>1</tpEmis><cDV>{chave[-1]}</cDV><tpAmb>{empresa.ambiente}</tpAmb><finNFe>1</finNFe><indFinal>1</indFinal><indPres>1</indPres><procEmi>0</procEmi><verProc>1.0.0</verProc></ide>'
    xml_puro += f'<emit><CNPJ>{empresa.cnpj}</CNPJ><xNome>{empresa.razao_social}</xNome><enderEmit><xLgr>{empresa.logradouro or "RUA"}</xLgr><nro>{empresa.numero or "SN"}</nro><xBairro>{empresa.bairro or "BAIRRO"}</xBairro><cMun>{ibge}</cMun><xMun>{empresa.municipio_nome or "CIDADE"}</xMun><UF>{empresa.uf or "SP"}</UF><CEP>{empresa.cep or "01000000"}</CEP><cPais>1058</cPais><xPais>BRASIL</xPais></enderEmit><IE>{empresa.inscricao_estadual}</IE><CRT>1</CRT></emit>'
    if venda.cliente:
        tag = "CNPJ" if len(venda.cliente.documento) > 11 else "CPF"
        xml_puro += f'<dest><{tag}>{venda.cliente.documento}</{tag}><xNome>{venda.cliente.nome}</xNome><indIEDest>9</indIEDest></dest>'
    
    for i, item in enumerate(venda.itens):
        x_prod = item.produto.descricao
        xml_puro += f'<det nItem="{i+1}"><prod><cProd>{item.id}</cProd><cEAN>SEM GTIN</cEAN><xProd>{x_prod}</xProd><NCM>{item.ncm or "21069029"}</NCM><CFOP>5102</CFOP><uCom>{item.produto.unidade}</uCom><qCom>{item.quantidade:.4f}</qCom><vUnCom>{item.preco_unitario:.4f}</vUnCom><vProd>{item.subtotal:.2f}</vProd><cEANTrib>SEM GTIN</cEANTrib><uTrib>{item.produto.unidade}</uTrib><qTrib>{item.quantidade:.4f}</qTrib><vUnTrib>{item.preco_unitario:.4f}</vUnTrib><indTot>1</indTot></prod><imposto><ICMS><ICMSSN102><orig>{item.origem or 0}</orig><CSOSN>102</CSOSN></ICMSSN102></ICMS><PIS><PISNT><CST>07</CST></PISNT></PIS><COFINS><COFINSNT><CST>07</CST></COFINSNT></COFINS></imposto></det>'
    
    xml_puro += f'<total><ICMSTot><vBC>0.00</vBC><vICMS>0.00</vICMS><vICMSDeson>0.00</vICMSDeson><vFCP>0.00</vFCP><vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST><vFCPSTRet>0.00</vFCPSTRet><vProd>{venda.total:.2f}</vProd><vFrete>0.00</vFrete><vSeg>0.00</vSeg><vDesc>0.00</vDesc><vII>0.00</vII><vIPI>0.00</vIPI><vIPIDevol>0.00</vIPIDevol><vPIS>0.00</vPIS><vCOFINS>0.00</vCOFINS><vOutro>0.00</vOutro><vNF>{venda.total:.2f}</vNF></ICMSTot></total>'
    xml_puro += '<transp><modFrete>9</modFrete></transp>'
    # BLOCO infAdic REMOVIDO PARA TESTE
    xml_puro += f'<pag><detPag><tPag>01</tPag><vPag>{venda.total:.2f}</vPag></detPag></pag></infNFe><infNFeSupl><qrCode>{qr}</qrCode><urlChave>{url.replace("qrcode", "consulta")}</urlChave></infNFeSupl></NFe>'
    
    # 2. Carga do Certificado
    cert_path = "/app/storage/certs/certificado.pfx" # Ajuste se necessário
    if not os.path.exists(cert_path):
        cert_path = os.path.join("/app/storage/certs", os.path.basename(empresa.certificado_path))
        
    with open(cert_path, "rb") as f: pfx_data = f.read()
    pw = empresa.certificado_senha.strip().encode('utf-8')
    
    # 3. Assinatura
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

    # 4. Envio
    url_s = "https://nfce.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx" if empresa.ambiente == 1 else "https://homologacao.nfce.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx"
    lote_xml = f'<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><idLote>40</idLote><indSinc>1</indSinc>{xml_assinado}</enviNFe>'
    env = f'<?xml version="1.0" encoding="utf-8"?><soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">{lote_xml}</nfeDadosMsg></soap12:Body></soap12:Envelope>'
    
    ct, kt = tempfile.NamedTemporaryFile(delete=False), tempfile.NamedTemporaryFile(delete=False)
    try:
        cert_pem = pcert.public_bytes(Encoding.PEM)
        for ot in others: cert_pem += ot.public_bytes(Encoding.PEM)
        ct.write(cert_pem); ct.close(); kt.write(pkey.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())); kt.close()
        
        res = requests.post(url=url_s, data=env.encode('utf-8'), headers={"Content-Type": "application/soap+xml; charset=utf-8"}, cert=(ct.name, kt.name), verify=False, timeout=30)
        
        print("RESPOSTA SEFAZ:")
        print(res.text)
        
        if "<cStat>100</cStat>" in res.text or "<cStat>204</cStat>" in res.text:
            print("SUCESSO! Atualizando banco...")
            nota.status_sefaz = "100"
            nota.motivo_sefaz = "Autorizado"
            nota.xml_enviado = xml_assinado
            nota.xml_recebido = res.text
            n_prot = re.search(r"<nProt>(.*?)</nProt>", res.text)
            if n_prot: nota.protocolo = n_prot.group(1)
            ch_nfe = re.search(r"<chNFe>(.*?)</chNFe>", res.text)
            if ch_nfe: nota.chave_acesso = ch_nfe.group(1)
            
            # Atualiza sequenciador
            empresa.ultimo_numero_nf = numero_nf
            venda.status = "PAGA"
            db.commit()
            print("BANCO ATUALIZADO!")
        else:
            print("FALHA AINDA PERSISTE.")
    finally:
        os.unlink(ct.name)
        os.unlink(kt.name)
        db.close()

if __name__ == "__main__":
    fix_and_emit_43()
