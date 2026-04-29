from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.usuario import Usuario, PapelUsuario
from app.core.security import verify_password, create_access_token, get_password_hash
from app.schemas.token import Token
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, Usuario as UsuarioSchema
from app.api.v1.deps import get_current_user, get_current_gerente
from app.core.limiter import limiter

router = APIRouter()

@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login_access_token(
    request: Request,
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

@router.get("/me", response_model=UsuarioSchema)
def read_current_user(current_user: Usuario = Depends(get_current_user)):
    """Retorna os dados do usuário logado."""
    return current_user

@router.get("/users", response_model=List[UsuarioSchema], dependencies=[get_current_gerente])
def list_users(db: Session = Depends(get_db)):
    """Lista todos os usuários. Apenas gerente."""
    return db.query(Usuario).order_by(Usuario.created_at.desc()).all()

@router.post("/register", response_model=UsuarioSchema, dependencies=[get_current_gerente])
def register_usuario(user_in: UsuarioCreate, db: Session = Depends(get_db)):
    """Cria um novo usuário. Apenas gerente pode executar."""
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
        papel=user_in.papel or PapelUsuario.GARCOM,
        is_active=1
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.put("/users/{user_id}", response_model=UsuarioSchema, dependencies=[get_current_gerente])
def update_usuario(user_id: int, user_in: UsuarioUpdate, db: Session = Depends(get_db)):
    """Atualiza dados de um usuário. Apenas gerente."""
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.password is not None:
        user.hashed_password = get_password_hash(user_in.password)
    if user_in.papel is not None:
        user.papel = user_in.papel
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    
    db.commit()
    db.refresh(user)
    return user
