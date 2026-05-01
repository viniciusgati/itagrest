import os
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
    current_user: Usuario = get_current_gerente
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


