from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.domain import VLAN, SwitchPort, Device
from app.schemas.domain import VLANCreate, VLANUpdate, VLANInDB
from app.services.audit import log_audit
from app.security.auth import RequireRole

router = APIRouter(prefix="/api/vlans", tags=["VLANs"])

@router.get("", response_model=List[VLANInDB])
def list_vlans(db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    return db.query(VLAN).filter(VLAN.unit_id == x_unit_id).order_by(VLAN.vlan_number).all()

@router.get("/{vlan_id}", response_model=VLANInDB)
def get_vlan(vlan_id: int, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    vlan = db.query(VLAN).filter(VLAN.id == vlan_id, VLAN.unit_id == x_unit_id).first()
    if not vlan:
        raise HTTPException(status_code=404, detail="VLAN não encontrada")
    return vlan

@router.post("", response_model=VLANInDB, status_code=201)
def create_vlan(payload: VLANCreate, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    existing = db.query(VLAN).filter(VLAN.vlan_number == payload.vlan_number, VLAN.unit_id == x_unit_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Já existe uma VLAN com o número {payload.vlan_number} na unidade")

    vlan = VLAN(**payload.model_dump(), unit_id=x_unit_id)
    db.add(vlan)
    db.commit()
    db.refresh(vlan)

    log_audit(
        db, action="CREATE", entity_type="VLAN", entity_id=vlan.id,
        entity_name=f"VLAN {vlan.vlan_number} ({vlan.name})", new_values=payload.model_dump()
    )
    return vlan

@router.put("/{vlan_id}", response_model=VLANInDB)
def update_vlan(vlan_id: int, payload: VLANUpdate, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    vlan = db.query(VLAN).filter(VLAN.id == vlan_id, VLAN.unit_id == x_unit_id).first()
    if not vlan:
        raise HTTPException(status_code=404, detail="VLAN não encontrada")

    if payload.vlan_number and payload.vlan_number != vlan.vlan_number:
        dup = db.query(VLAN).filter(VLAN.vlan_number == payload.vlan_number, VLAN.unit_id == x_unit_id).first()
        if dup:
            raise HTTPException(status_code=400, detail=f"Já existe uma VLAN com o número {payload.vlan_number} na unidade")

    prev = {"vlan_number": vlan.vlan_number, "name": vlan.name}
    update_data = payload.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        setattr(vlan, field, val)

    db.commit()
    db.refresh(vlan)

    log_audit(
        db, action="UPDATE", entity_type="VLAN", entity_id=vlan.id,
        entity_name=f"VLAN {vlan.vlan_number}", previous_values=prev, new_values=update_data
    )
    return vlan

@router.delete("/{vlan_id}")
def delete_vlan(vlan_id: int, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    vlan = db.query(VLAN).filter(VLAN.id == vlan_id, VLAN.unit_id == x_unit_id).first()
    if not vlan:
        raise HTTPException(status_code=404, detail="VLAN não encontrada")

    ports_count = db.query(SwitchPort).filter(SwitchPort.vlan_id == vlan_id).count()
    devices_count = db.query(Device).filter(Device.vlan_id == vlan_id).count()

    if ports_count > 0 or devices_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir a VLAN {vlan.vlan_number} pois ela está em uso por {ports_count} porta(s) e {devices_count} equipamento(s)."
        )

    log_audit(
        db, action="DELETE", entity_type="VLAN", entity_id=vlan.id,
        entity_name=f"VLAN {vlan.vlan_number}", previous_values={"vlan_number": vlan.vlan_number, "name": vlan.name}
    )

    db.delete(vlan)
    db.commit()
    return {"message": "VLAN excluída com sucesso"}
