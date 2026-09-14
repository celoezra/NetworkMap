from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.domain import User, Role, UserUnitAccess, Unit, AuditLog
from app.security.auth import get_current_user, RequireRole
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["Users"])

class UserStatusUpdate(BaseModel):
    status: str # ACTIVE, BLOCKED, REVOKED

class UserUnitAccessCreate(BaseModel):
    unit_id: int
    role_name: str # ADMIN, TECNICO, VISUALIZACAO

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    status: str
    global_role: str
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["ADMIN"])) # Note: Global role check handles SUPERADMIN implicitly inside RequireRole
):
    """SUPERADMIN pode ver todos."""
    if current_user.global_role != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="Apenas SUPERADMIN pode gerenciar usuários globalmente.")
    
    users = db.query(User).all()
    return users

@router.put("/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["ADMIN"]))
):
    if current_user.global_role != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
    if payload.status not in ["ACTIVE", "BLOCKED", "REVOKED"]:
        raise HTTPException(status_code=400, detail="Status inválido.")

    old_status = user.status
    user.status = payload.status
    
    # Audit log
    audit = AuditLog(
        actor_user_id=current_user.id,
        action=f"USER_{payload.status}",
        entity_type="User",
        entity_id=user.id,
        entity_name=user.email,
        previous_values=old_status,
        new_values=payload.status
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Status atualizado com sucesso", "status": user.status}

@router.post("/{user_id}/units")
def assign_unit_access(
    user_id: int,
    payload: UserUnitAccessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["ADMIN"]))
):
    if current_user.global_role != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="Acesso negado.")

    user = db.query(User).filter(User.id == user_id).first()
    unit = db.query(Unit).filter(Unit.id == payload.unit_id).first()
    role = db.query(Role).filter(Role.name == payload.role_name).first()

    if not user or not unit or not role:
        raise HTTPException(status_code=404, detail="Usuário, Unidade ou Perfil não encontrado.")
        
    access = db.query(UserUnitAccess).filter(
        UserUnitAccess.user_id == user.id,
        UserUnitAccess.unit_id == unit.id
    ).first()

    if access:
        access.role_id = role.id
        access.active = True
    else:
        access = UserUnitAccess(
            user_id=user.id,
            unit_id=unit.id,
            role_id=role.id
        )
        db.add(access)

    audit = AuditLog(
        actor_user_id=current_user.id,
        unit_id=unit.id,
        action="UNIT_ACCESS_UPDATED",
        entity_type="UserUnitAccess",
        entity_id=user.id,
        entity_name=user.email,
        new_values=f"Role: {role.name}"
    )
    db.add(audit)
    db.commit()

    return {"message": "Acesso à unidade concedido com sucesso."}

@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna dados do usuário atual e suas permissões nas unidades."""
    access_list = db.query(UserUnitAccess).filter(UserUnitAccess.user_id == current_user.id, UserUnitAccess.active == True).all()
    
    units = []
    for access in access_list:
        unit = db.query(Unit).filter(Unit.id == access.unit_id).first()
        role = db.query(Role).filter(Role.id == access.role_id).first()
        if unit and role:
            units.append({
                "unit_id": unit.id,
                "unit_name": unit.name,
                "role": role.name
            })
            
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "global_role": current_user.global_role,
        "units": units
    }
