from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.models.domain import Rack, Switch
from app.schemas.domain import RackCreate, RackUpdate, RackInDB
from app.services.audit import log_audit
from app.security.auth import RequireRole

router = APIRouter(prefix="/api/racks", tags=["Racks"])

@router.get("", response_model=List[RackInDB])
def list_racks(db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    return db.query(Rack).filter(Rack.unit_id == x_unit_id).all()

@router.get("/{rack_id}", response_model=RackInDB)
def get_rack(rack_id: int, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    rack = db.query(Rack).filter(Rack.id == rack_id, Rack.unit_id == x_unit_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack não encontrado")
    return rack

@router.post("", response_model=RackInDB, status_code=201)
def create_rack(payload: RackCreate, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    existing = db.query(Rack).filter(Rack.name == payload.name, Rack.unit_id == x_unit_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Já existe um rack com este nome na unidade selecionada")
    
    rack = Rack(**payload.model_dump(), unit_id=x_unit_id)
    db.add(rack)
    db.commit()
    db.refresh(rack)

    log_audit(
        db,
        action="CREATE",
        entity_type="Rack",
        entity_id=rack.id,
        entity_name=rack.name,
        new_values=payload.model_dump()
    )

    return rack

@router.put("/{rack_id}", response_model=RackInDB)
def update_rack(rack_id: int, payload: RackUpdate, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    rack = db.query(Rack).filter(Rack.id == rack_id, Rack.unit_id == x_unit_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack não encontrado")

    if payload.name and payload.name != rack.name:
        dup = db.query(Rack).filter(Rack.name == payload.name, Rack.unit_id == x_unit_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="Já existe um rack com este nome na unidade selecionada")

    prev_data = {"name": rack.name, "location_description": rack.location_description, "description": rack.description}
    update_data = payload.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        setattr(rack, field, val)

    db.commit()
    db.refresh(rack)

    log_audit(
        db,
        action="UPDATE",
        entity_type="Rack",
        entity_id=rack.id,
        entity_name=rack.name,
        previous_values=prev_data,
        new_values=update_data
    )

    return rack

@router.delete("/{rack_id}")
def delete_rack(rack_id: int, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    rack = db.query(Rack).filter(Rack.id == rack_id, Rack.unit_id == x_unit_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack não encontrado")

    switches_count = db.query(Switch).filter(Switch.rack_id == rack_id).count()
    if switches_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir o rack '{rack.name}' pois ele possui {switches_count} switch(es) vinculado(s)."
        )

    log_audit(
        db,
        action="DELETE",
        entity_type="Rack",
        entity_id=rack.id,
        entity_name=rack.name,
        previous_values={"name": rack.name, "location_description": rack.location_description}
    )

    db.delete(rack)
    db.commit()
    return {"message": "Rack excluído com sucesso"}
