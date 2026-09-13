from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.domain import Location, Device, SwitchPort
from app.schemas.domain import LocationCreate, LocationUpdate, LocationInDB
from app.services.audit import log_audit

router = APIRouter(prefix="/api/locations", tags=["Locations"])

@router.get("", response_model=List[LocationInDB])
def list_locations(db: Session = Depends(get_db)):
    return db.query(Location).all()

@router.get("/{location_id}", response_model=LocationInDB)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Local não encontrado")
    return loc

@router.post("", response_model=LocationInDB, status_code=201)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    existing = db.query(Location).filter(Location.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Já existe um local com este nome")

    loc = Location(**payload.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)

    log_audit(
        db, action="CREATE", entity_type="Location", entity_id=loc.id,
        entity_name=loc.name, new_values=payload.model_dump()
    )
    return loc

@router.put("/{location_id}", response_model=LocationInDB)
def update_location(location_id: int, payload: LocationUpdate, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Local não encontrado")

    if payload.name and payload.name != loc.name:
        dup = db.query(Location).filter(Location.name == payload.name).first()
        if dup:
            raise HTTPException(status_code=400, detail="Já existe um local com este nome")

    prev = {"name": loc.name, "sector": loc.sector, "floor": loc.floor}
    update_data = payload.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        setattr(loc, field, val)

    db.commit()
    db.refresh(loc)

    log_audit(
        db, action="UPDATE", entity_type="Location", entity_id=loc.id,
        entity_name=loc.name, previous_values=prev, new_values=update_data
    )
    return loc

@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Local não encontrado")

    devices_count = db.query(Device).filter(Device.location_id == location_id).count()
    ports_count = db.query(SwitchPort).filter(SwitchPort.destination_location_id == location_id).count()

    if devices_count > 0 or ports_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir o local '{loc.name}' pois ele possui {devices_count} equipamento(s) e {ports_count} porta(s) associada(s)."
        )

    log_audit(
        db, action="DELETE", entity_type="Location", entity_id=loc.id,
        entity_name=loc.name, previous_values={"name": loc.name}
    )

    db.delete(loc)
    db.commit()
    return {"message": "Local excluído com sucesso"}
