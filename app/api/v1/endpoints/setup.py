from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.usuario import Usuario, PapelUsuario
from app.schemas.usuario import UsuarioCreate, Usuario as UsuarioSchema
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/status", response_model=dict)
def check_setup_status(db: Session = Depends(get_db)):
    """Verifica se o sistema já possui usuários (se o bootstrap é necessário)."""
    user_exists = db.query(Usuario).first() is not None
    return {"setup_needed": not user_exists}

@router.post("/setup-admin", response_model=UsuarioSchema)
def setup_admin(user_in: UsuarioCreate, db: Session = Depends(get_db)):
    """Cria o primeiro usuário administrador do sistema (Apenas se não houver usuários)."""
    # 1. Verificar se já existem usuários
    if db.query(Usuario).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O sistema já foi configurado. Bootstrap desativado."
        )
    
    # 2. Criar novo admin
    new_admin = Usuario(
        full_name=user_in.full_name,
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        papel=PapelUsuario.GERENTE,
        is_active=1
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    
    return new_admin
