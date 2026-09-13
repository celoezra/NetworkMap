from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.models.domain import Device, SwitchPort, Location, VLAN, PortStatus
from app.schemas.domain import DeviceCreate, DeviceUpdate, DeviceInDB
from app.services.audit import log_audit

router = APIRouter(prefix="/api/devices", tags=["Devices"])

def enrich_device(device: Device, db: Session) -> DeviceInDB:
    connected_port = db.query(SwitchPort).filter(
        SwitchPort.connected_device_id == device.id
    ).first()

    return DeviceInDB(
        id=device.id,
        name=device.name,
        hostname=device.hostname,
        ip_address=device.ip_address,
        mac_address=device.mac_address,
        device_type=device.device_type,
        location_id=device.location_id,
        vlan_id=device.vlan_id,
        manufacturer=device.manufacturer,
        model=device.model,
        asset_tag=device.asset_tag,
        serial_number=device.serial_number,
        description=device.description,
        notes=device.notes,
        created_at=device.created_at,
        updated_at=device.updated_at,
        location_name=device.location.name if device.location else None,
        vlan_name=device.vlan.name if device.vlan else None,
        connected_switch_id=connected_port.switch_id if connected_port else None,
        connected_switch_name=connected_port.switch.name if connected_port and connected_port.switch else None,
        connected_port_number=connected_port.port_number if connected_port else None
    )

@router.get("", response_model=List[DeviceInDB])
def list_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return [enrich_device(d, db) for d in devices]

@router.get("/{device_id}", response_model=DeviceInDB)
def get_device(device_id: int, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    return enrich_device(dev, db)

@router.post("", response_model=DeviceInDB, status_code=201)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    switch_id = payload.switch_id
    port_id = payload.port_id
    
    dev_data = payload.model_dump(exclude={"switch_id", "port_id"})
    device = Device(**dev_data)
    db.add(device)
    db.commit()
    db.refresh(device)

    if port_id:
        port = db.query(SwitchPort).filter(SwitchPort.id == port_id).first()
        if port:
            port.connected_device_id = device.id
            port.status = PortStatus.CONNECTED.value
            if device.location_id:
                port.destination_location_id = device.location_id
            if device.vlan_id:
                port.vlan_id = device.vlan_id
            db.commit()

    log_audit(
        db, action="CREATE", entity_type="Device", entity_id=device.id,
        entity_name=device.name, new_values=payload.model_dump()
    )

    return enrich_device(device, db)

@router.put("/{device_id}", response_model=DeviceInDB)
def update_device(device_id: int, payload: DeviceUpdate, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")

    prev = {"name": dev.name, "ip_address": dev.ip_address, "location_id": dev.location_id}
    update_data = payload.model_dump(exclude_unset=True)

    for field, val in update_data.items():
        setattr(dev, field, val)

    db.commit()
    db.refresh(dev)

    log_audit(
        db, action="UPDATE", entity_type="Device", entity_id=dev.id,
        entity_name=dev.name, previous_values=prev, new_values=update_data
    )

    return enrich_device(dev, db)

@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == device_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")

    # Clear references from switch ports
    ports = db.query(SwitchPort).filter(SwitchPort.connected_device_id == device_id).all()
    for p in ports:
        p.connected_device_id = None
        p.status = PortStatus.FREE.value
    db.commit()

    log_audit(
        db, action="DELETE", entity_type="Device", entity_id=dev.id,
        entity_name=dev.name, previous_values={"name": dev.name, "ip_address": dev.ip_address}
    )

    db.delete(dev)
    db.commit()
    return {"message": "Equipamento excluído com sucesso"}
