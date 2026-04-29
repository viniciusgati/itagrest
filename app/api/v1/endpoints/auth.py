from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.usuario import Usuario, PapelUsuario
from app.core.security import verify_password, create_access_token, get_password_hash
from app.schemas.token import Token
from app.schemas.usuario import UsuarioCreate, Usuario as UsuarioSchema
from app.api.v1.deps import get_current_gerente

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """OAuth2 compatible token login, get an access token for future requests."""
    user = db.query(Usuario).filter(Usuario.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo"
        )
    
    return {
        "access_token": create_access_token(
            user.id, 
            extra_claims={"papel": user.papel}
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UsuarioSchema, dependencies=[get_current_gerente])
def register_usuario(user_in: UsuarioCreate, db: Session = Depends(get_db)):
    """Cria um novo usuário (garçom). Apenas gerente pode executar."""
    existing = db.query(Usuario).filter(
        (Usuario.username == user_in.username) | (Usuario.email == user_in.email)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário ou email já cadastrado"
        )
    
    new_user = Usuario(
        full_name=user_in.full_name,
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        papel=PapelUsuario.GARCOM,
        is_active=1
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user
