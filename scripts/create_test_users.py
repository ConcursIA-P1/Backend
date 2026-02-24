#!/usr/bin/env python3
"""
Script para criar usuários de teste no banco de dados.
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from src.config.database import SessionLocal
from src.models.user import User, UserRole
from src.services.auth_service import AuthService


def create_test_users():
    """Cria usuários de teste no banco."""
    db = SessionLocal()
    
    try:
        # Verificar se usuários já existem
        existing_student = db.query(User).filter(User.email == "maria@teste.com").first()
        existing_teacher = db.query(User).filter(User.email == "joao@teste.com").first()
        
        if existing_student and existing_teacher:
            print("✓ Usuários de teste já existem no banco de dados")
            return
        
        # Criar usuários
        auth_service = AuthService(db)
        
        # Aluna
        if not existing_student:
            student = db.query(User).filter(User.email == "maria@teste.com").first()
            if not student:
                password_hash = AuthService.hash_password("senha123")
                student = User(
                    email="maria@teste.com",
                    name="Maria Silva",
                    password_hash=password_hash,
                    role=UserRole.ALUNO
                )
                db.add(student)
                print("✓ Usuária Maria Silva criada")
        
        # Professor
        if not existing_teacher:
            teacher = db.query(User).filter(User.email == "joao@teste.com").first()
            if not teacher:
                password_hash = AuthService.hash_password("senha123")
                teacher = User(
                    email="joao@teste.com",
                    name="Prof. João Santos",
                    password_hash=password_hash,
                    role=UserRole.PROFESSOR
                )
                db.add(teacher)
                print("✓ Professor João Santos criado")
        
        db.commit()
        print("\n✓ Usuários de teste criados com sucesso!")
        print("\nCredenciais de teste:")
        print("  Aluna: maria@teste.com / senha123")
        print("  Professor: joao@teste.com / senha123")
        
    except Exception as e:
        print(f"✗ Erro ao criar usuários: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
