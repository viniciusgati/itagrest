import os, socket, ssl, time, re, requests
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.venda import Venda, StatusVenda
from app.models.nota_fiscal import NotaFiscal as NotaFiscalModel
from app.services.sefaz import SefazService
from pydantic import BaseModel
from datetime import datetime
from app.api.v1.deps import get_current_user, get_current_user_query_token, get_current_gerente
from app.models.usuario import Usuario

router = APIRouter()

class NotaFiscalResponse(BaseModel):
    venda_id: int
    chave_acesso: Optional[str] = None
    protocolo: Optional[str] = None
    status_sefaz: Optional[str] = None
    motivo_sefaz: Optional[str] = None
    numero_nota: Optional[int] = None
    logs_transmissao: Optional[str] = None
    xml_enviado: Optional[str] = None
    xml_recebido: Optional[str] = None
    xml_autorizado: Optional[str] = None
    protocolo_cancelamento: Optional[str] = None
    motivo_cancelamento: Optional[str] = None
    data_cancelamento: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.post("/emitir/{venda_id}", response_model=NotaFiscalResponse)
def emitir_nota(
    venda_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Aciona a geração e transmissão da NFC-e. 
    Este endpoint é resiliente: se a SEFAZ falhar, ele retorna a nota com status de erro
    em vez de lançar uma exceção 400, permitindo que o fluxo da venda continue.
    """
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    nota_existente = db.query(NotaFiscalModel).filter(
        NotaFiscalModel.venda_id == venda_id,
        NotaFiscalModel.status_sefaz == '100'
    ).first()
    if nota_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta venda já possui uma NFC-e autorizada pela SEFAZ. Não é possível emitir novamente."
        )
    nota_cancelada = db.query(NotaFiscalModel).filter(
        NotaFiscalModel.venda_id == venda_id,
        NotaFiscalModel.protocolo_cancelamento.isnot(None)
    ).first()
    if nota_cancelada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta venda possui uma NFC-e cancelada. Não é possível emitir novamente."
        )
    
    try:
        # Tenta emitir via SefazService
        nota = SefazService.emitir_nfce(db, venda)
        return nota
    except Exception as e:
        # Em caso de qualquer erro (timeout, certificado, etc), busca o registro da nota 
        # que o SefazService criou/atualizou com o erro e retorna ela.
        db.rollback()
        nota_com_erro = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        if nota_com_erro:
            return nota_com_erro
            
        # Fallback caso nem o registro da nota tenha sido criado
        return NotaFiscalResponse(
            venda_id=venda_id,
            status_sefaz="ERRO",
            motivo_sefaz=str(e)
        )

class CancelamentoRequest(BaseModel):
    justificativa: str

@router.post("/cancelar/{venda_id}", response_model=NotaFiscalResponse)
def cancelar_nota(
    venda_id: int,
    body: CancelamentoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    justificativa = body.justificativa.strip()
    if len(justificativa) < 15:
        raise HTTPException(status_code=400, detail="Justificativa deve ter no mínimo 15 caracteres.")
    try:
        nota = SefazService.cancelar_nfce(db, venda_id, justificativa)
        return nota
    except Exception as e:
        db.rollback()
        nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        if nota:
            return nota
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/todas", response_model=List[NotaFiscalResponse])
def list_notas(
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Lista todas as notas fiscais emitidas."""
    return db.query(NotaFiscalModel).order_by(NotaFiscalModel.data_emissao.desc()).all()

@router.get("/{venda_id}/imprimir")
def imprimir_danfe(
    venda_id: int, 
    largura: int = 80, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user_query_token)
):
    """
    Gera e retorna o PDF da DANFE para impressão.
    largura: 80 para bobinas de 80mm, 58 para bobinas de 58mm.
    """
    try:
        from fastapi.responses import StreamingResponse
        pdf_buffer = SefazService.gerar_danfe_pdf(db, venda_id, largura)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=danfe_{venda_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{venda_id}/imprimir-a4")
def imprimir_danfe_a4(
    venda_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user_query_token)
):
    """
    Gera e retorna o PDF da DANFE completa (A4) para impressão.
    """
    try:
        from fastapi.responses import StreamingResponse
        pdf_buffer = SefazService.gerar_danfe_a4(db, venda_id)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=danfe_a4_{venda_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{venda_id}", response_model=NotaFiscalResponse)
def get_nota_venda(
    venda_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Consulta o status fiscal de uma venda."""
    nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
    if not nota:
        raise HTTPException(status_code=404, detail="Status fiscal não encontrado para esta venda")
    return nota

@router.get("/{venda_id}/xml-log")
def get_xml_log(
    venda_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Retorna os logs e todos os XMLs (enviado, recebido, autorizado) de uma nota."""
    nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
    if not nota:
        raise HTTPException(status_code=404, detail="Nota não encontrada para esta venda")
        
    return {
        "xml_enviado": nota.xml_enviado,
        "xml_recebido": nota.xml_recebido,
        "xml_autorizado": nota.xml_autorizado,
        "logs": nota.logs_transmissao
    }

@router.get("/diagnostico/sefaz")
def diagnosticar_sefaz(
    db: Session = Depends(get_db),
    current_user: Usuario = get_current_gerente
):
    """Diagnostico de conectividade com a SEFAZ SP."""
    host_prod = "nfce.fazenda.sp.gov.br"
    host_homol = "homologacao.nfce.fazenda.sp.gov.br"
    port = 443
    resultados = {}

    for label, host in [("producao", host_prod), ("homologacao", host_homol)]:
        r = {"host": host, "erros": []}
        try:
            ip = socket.gethostbyname(host)
            r["dns"] = ip
        except Exception as e:
            r["dns"] = f"FALHA: {e}"
            r["erros"].append(f"DNS: {e}")

        try:
            start = time.time()
            sock = socket.create_connection((host, port), timeout=10)
            r["tcp"] = f"OK ({((time.time()-start)*1000):.0f}ms)"
            sock.close()
        except Exception as e:
            r["tcp"] = f"FALHA: {e}"
            r["erros"].append(f"TCP: {e}")

        try:
            ctx = ssl.create_default_context()
            start = time.time()
            with ctx.wrap_socket(socket.create_connection((host, port), timeout=10), server_hostname=host) as s:
                r["tls"] = f"OK ({((time.time()-start)*1000):.0f}ms)"
                r["tls_version"] = s.version()
        except Exception as e:
            r["tls"] = f"FALHA: {e}"
            r["erros"].append(f"TLS: {e}")

        resultados[label] = r

    # Teste real: exatamente como a emissao faz, com certificado digital
    try:
        import tempfile
        from app.models.empresa import Empresa
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
        from cryptography.hazmat.backends import default_backend

        empresa = db.query(Empresa).first()
        if not empresa or not empresa.certificado_path:
            resultados["certificado"] = {"status": "FALHA", "erro": "Empresa nao configurada ou sem certificado"}
        else:
            cert_path = os.path.join("storage/certs", os.path.basename(empresa.certificado_path))
            resultados["certificado"] = {"path": cert_path, "cnpj": empresa.cnpj, "ambiente": empresa.ambiente}

            try:
                with open(cert_path, "rb") as f:
                    pfx_data = f.read()
                pw = (empresa.certificado_senha or "").strip().encode("utf-8")
                p12 = pkcs12.load_key_and_certificates(pfx_data, pw, default_backend())
                pkey, pcert, others = (p12[0], p12[1], p12[2]) if isinstance(p12, tuple) else (p12.key, p12.cert, p12.othercerts)
                resultados["certificado"]["validade"] = str(pcert.not_valid_after_utc)
                resultados["certificado"]["status"] = "OK"

                # Testa POST com requests + certificado (igual a emissao real)
                url_s = "https://nfce.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx" if empresa.ambiente == 1 else "https://homologacao.nfce.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx"
                env = f'<?xml version="1.0" encoding="utf-8"?><soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"><enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><idLote>999999</idLote><indSinc>0</indSinc></enviNFe></nfeDadosMsg></soap12:Body></soap12:Envelope>'

                ct, kt = tempfile.NamedTemporaryFile(delete=False), tempfile.NamedTemporaryFile(delete=False)
                try:
                    cert_pem = pcert.public_bytes(Encoding.PEM)
                    for ot in others:
                        cert_pem += ot.public_bytes(Encoding.PEM)
                    ct.write(cert_pem); ct.close()
                    kt.write(pkey.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())); kt.close()

                    start = time.time()
                    res = requests.post(url=url_s, data=env.encode("utf-8"),
                        headers={"Content-Type": "application/soap+xml; charset=utf-8"},
                        cert=(ct.name, kt.name), verify=False, timeout=15)
                    elapsed = (time.time() - start) * 1000
                    resultados["emissao_teste"] = {
                        "url": url_s,
                        "tempo_ms": f"{elapsed:.0f}",
                        "http_status": res.status_code,
                        "resposta_tamanho": len(res.text),
                    }
                    if "<cStat>" in res.text:
                        cstat = re.search(r"<cStat>(\d+)</cStat>", res.text)
                        xmotivo = re.search(r"<xMotivo>(.*?)</xMotivo>", res.text)
                        resultados["emissao_teste"]["cStat"] = cstat.group(1) if cstat else "N/A"
                        resultados["emissao_teste"]["xMotivo"] = xmotivo.group(1) if xmotivo else "N/A"
                    resultados["emissao_teste"]["status"] = "OK"
                finally:
                    for x in [ct.name, kt.name]:
                        if os.path.exists(x): os.remove(x)
            except Exception as e:
                resultados["certificado"]["status"] = f"FALHA: {type(e).__name__}: {str(e)}"
    except Exception as e:
        resultados["certificado"] = {"status": "FALHA", "erro": f"{type(e).__name__}: {str(e)}"}

    return {"status": "ok", "resultados": resultados, "timestamp": datetime.now().isoformat()}


