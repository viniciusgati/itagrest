import os
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.venda import Venda, StatusVenda
from app.models.nota_fiscal import NotaFiscal as NotaFiscalModel
from app.services.sefaz import SefazService
from pydantic import BaseModel

router = APIRouter()

class NotaFiscalResponse(BaseModel):
    venda_id: int
    chave_acesso: Optional[str] = None
    protocolo: Optional[str] = None
    status_sefaz: Optional[str] = None
    motivo_sefaz: Optional[str] = None
    numero_nota: Optional[int] = None
    logs_transmissao: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.post("/emitir/{venda_id}", response_model=NotaFiscalResponse)
def emitir_nota(venda_id: int, db: Session = Depends(get_db)):
    """
    Aciona a geração e transmissão da NFC-e para uma venda fechada.
    Garante que erros sejam capturados e salvos no banco para auditoria.
    """
    venda = db.query(Venda).filter(Venda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    if venda.status != StatusVenda.PAGA:
        raise HTTPException(
            status_code=400, 
            detail="A venda deve estar PAGA para emitir a NFC-e"
        )
    
    try:
        # Transmitir via SefazService
        nota = SefazService.emitir_nfce(db, venda)
        return nota
    except Exception as e:
        # Busca a nota para retornar o que foi gravado (mesmo com erro)
        nota_com_erro = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
        if nota_com_erro:
            return nota_com_erro
            
        raise HTTPException(
            status_code=400, 
            detail=f"Erro na transmissão SEFAZ: {str(e)}"
        )

@router.get("/todas", response_model=List[NotaFiscalResponse])
def list_notas(db: Session = Depends(get_db)):
    """Lista todas as notas fiscais emitidas."""
    return db.query(NotaFiscalModel).order_by(NotaFiscalModel.data_emissao.desc()).all()

@router.get("/{venda_id}/imprimir")
def imprimir_danfe(venda_id: int, db: Session = Depends(get_db)):
    """Gera e retorna o PDF da DANFE para impressão."""
    try:
        from fastapi.responses import StreamingResponse
        pdf_buffer = SefazService.gerar_danfe_pdf(db, venda_id)
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=danfe_{venda_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{venda_id}", response_model=NotaFiscalResponse)
def get_nota_venda(venda_id: int, db: Session = Depends(get_db)):
    """Consulta o status fiscal de uma venda."""
    nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
    if not nota:
        raise HTTPException(status_code=404, detail="Status fiscal não encontrado para esta venda")
    return nota

@router.get("/{venda_id}/xml-log")
def get_xml_log(venda_id: int, db: Session = Depends(get_db)):
    """Retorna o conteúdo do XML e os logs salvos no banco de dados."""
    nota = db.query(NotaFiscalModel).filter(NotaFiscalModel.venda_id == venda_id).first()
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada para esta venda")
    
    return {
        "xml": nota.xml_autorizado,
        "logs": nota.logs_transmissao
    }

