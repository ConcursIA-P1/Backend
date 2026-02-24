"""
Endpoints de autenticação (login e cadastro).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.services.auth_service import AuthService
from src.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, AuthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    summary="Registrar novo usuário"
)
def register(
    data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário na plataforma.
    
    - **email**: Email único do usuário
    - **name**: Nome completo
    - **password**: Senha (mínimo 8 caracteres)
    - **role**: Tipo de conta (aluno ou professor)
    """
    try:
        service = AuthService(db)
        user = service.register(data)
        
        # Criar token automaticamente após registro
        token = service.create_token(user.id)
        
        return AuthResponse(
            success=True,
            message="Cadastro realizado com sucesso",
            user=user,
            token=token
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao registrar usuário: {str(e)}")


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Fazer login"
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Autentica usuário e retorna token de acesso.
    
    - **email**: Email registrado
    - **password**: Senha
    """
    try:
        service = AuthService(db)
        result = service.login(data)
        
        return AuthResponse(
            success=True,
            message="Login realizado com sucesso",
            user=result["user"],
            token=result["access_token"]
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao fazer login")


@router.get(
    "/verify-token",
    summary="Verificar token"
)
def verify_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verifica se um token é válido.
    
    - **token**: JWT token a verificar
    """
    service = AuthService(db)
    user_id = service.verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    return {
        "valid": True,
        "user_id": user_id,
        "message": "Token é válido"
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obter perfil do usuário autenticado"
)
def get_current_user(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Retorna informações do usuário autenticado.
    
    - **token**: JWT token (passar no header Authorization: Bearer <token>)
    """
    service = AuthService(db)
    user_id = service.verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    from src.repositories.user_repository import UserRepository
    from uuid import UUID
    
    repo = UserRepository(db)
    user = repo.get_by_id(UUID(user_id))
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role.value,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )
