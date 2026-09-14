from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.models.domain import Switch, SwitchPort, Rack, VLAN, Location, Device, PortStatus
from app.schemas.domain import (
    SwitchCreate, SwitchUpdate, SwitchInDB,
    SwitchPortUpdate, SwitchPortInDB
)
from app.services.audit import log_audit
from app.security.auth import RequireRole

router = APIRouter(prefix="/api/switches", tags=["Switches"])

def enrich_port(port: SwitchPort, db: Session) -> SwitchPortInDB:
    p_dict = {
        "id": port.id,
        "switch_id": port.switch_id,
        "port_number": port.port_number,
        "name": port.name,
        "description": port.description,
        "vlan_id": port.vlan_id,
        "destination_location_id": port.destination_location_id,
        "connected_device_id": port.connected_device_id,
        "connection_type": port.connection_type,
        "status": port.status,
        "notes": port.notes,
        "created_at": port.created_at,
        "updated_at": port.updated_at,
        "vlan_number": port.vlan.vlan_number if port.vlan else None,
        "vlan_name": port.vlan.name if port.vlan else None,
        "destination_location_name": port.destination_location.name if port.destination_location else None,
        "connected_device_name": port.connected_device.name if port.connected_device else None,
        "connected_device_ip": port.connected_device.ip_address if port.connected_device else None,
        "connected_device_mac": port.connected_device.mac_address if port.connected_device else None,
    }
    return SwitchPortInDB(**p_dict)

def enrich_switch(sw: Switch, db: Session) -> SwitchInDB:
    ports_enriched = [enrich_port(p, db) for p in sw.ports]
    return SwitchInDB(
        id=sw.id,
        name=sw.name,
        hostname=sw.hostname,
        manufacturer=sw.manufacturer,
        model=sw.model,
        ip_address=sw.ip_address,
        mac_address=sw.mac_address,
        port_count=sw.port_count,
        rack_id=sw.rack_id,
        rack_position=sw.rack_position,
        notes=sw.notes,
        created_at=sw.created_at,
        updated_at=sw.updated_at,
        rack_name=sw.rack.name if sw.rack else None,
        ports=ports_enriched
    )

@router.get("", response_model=List[SwitchInDB])
def list_switches(db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    switches = db.query(Switch).filter(Switch.unit_id == x_unit_id).all()
    return [enrich_switch(sw, db) for sw in switches]

@router.get("/{switch_id}", response_model=SwitchInDB)
def get_switch(switch_id: int, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    sw = db.query(Switch).filter(Switch.id == switch_id, Switch.unit_id == x_unit_id).first()
    if not sw:
        raise HTTPException(status_code=404, detail="Switch não encontrado")
    return enrich_switch(sw, db)

@router.post("", response_model=SwitchInDB, status_code=201)
def create_switch(payload: SwitchCreate, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    existing = db.query(Switch).filter(Switch.hostname == payload.hostname, Switch.unit_id == x_unit_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Já existe um switch com este Hostname na unidade")

    sw = Switch(**payload.model_dump(), unit_id=x_unit_id)
    db.add(sw)
    db.commit()
    db.refresh(sw)

    # Auto generate ports 1..N
    for p in range(1, sw.port_count + 1):
        port = SwitchPort(
            switch_id=sw.id,
            port_number=p,
            status=PortStatus.FREE.value,
            connection_type="Access",
            unit_id=x_unit_id
        )
        db.add(port)
    db.commit()
    db.refresh(sw)

    log_audit(
        db,
        action="CREATE",
        entity_type="Switch",
        entity_id=sw.id,
        entity_name=sw.name,
        new_values=payload.model_dump()
    )

    return enrich_switch(sw, db)

@router.put("/{switch_id}", response_model=SwitchInDB)
def update_switch(switch_id: int, payload: SwitchUpdate, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    sw = db.query(Switch).filter(Switch.id == switch_id, Switch.unit_id == x_unit_id).first()
    if not sw:
        raise HTTPException(status_code=404, detail="Switch não encontrado")

    if payload.hostname and payload.hostname != sw.hostname:
        dup = db.query(Switch).filter(Switch.hostname == payload.hostname, Switch.unit_id == x_unit_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="Já existe um switch com este Hostname na unidade")

    prev_data = {"name": sw.name, "hostname": sw.hostname, "port_count": sw.port_count}
    update_data = payload.model_dump(exclude_unset=True)

    old_port_count = sw.port_count
    for field, val in update_data.items():
        setattr(sw, field, val)

    # Adjust ports if port_count changed
    if payload.port_count and payload.port_count != old_port_count:
        if payload.port_count > old_port_count:
            # Add new ports
            for p in range(old_port_count + 1, payload.port_count + 1):
                port = SwitchPort(switch_id=sw.id, port_number=p, status=PortStatus.FREE.value, unit_id=sw.unit_id)
                db.add(port)
        else:
            # Remove excess ports
            db.query(SwitchPort).filter(
                SwitchPort.switch_id == sw.id,
                SwitchPort.port_number > payload.port_count
            ).delete()

    db.commit()
    db.refresh(sw)

    log_audit(
        db,
        action="UPDATE",
        entity_type="Switch",
        entity_id=sw.id,
        entity_name=sw.name,
        previous_values=prev_data,
        new_values=update_data
    )

    return enrich_switch(sw, db)

@router.delete("/{switch_id}")
def delete_switch(switch_id: int, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    sw = db.query(Switch).filter(Switch.id == switch_id, Switch.unit_id == x_unit_id).first()
    if not sw:
        raise HTTPException(status_code=404, detail="Switch não encontrado")

    # Check how many configured ports exist
    used_ports = db.query(SwitchPort).filter(
        SwitchPort.switch_id == switch_id,
        SwitchPort.status != PortStatus.FREE.value
    ).count()

    log_audit(
        db,
        action="DELETE",
        entity_type="Switch",
        entity_id=sw.id,
        entity_name=sw.name,
        previous_values={"name": sw.name, "hostname": sw.hostname, "used_ports": used_ports}
    )

    db.delete(sw) # Cascades delete to switch_ports
    db.commit()
    return {"message": "Switch e suas portas excluídos com sucesso", "used_ports_warning": used_ports}

# --- SWITCH PORT UPDATE ENDPOINT ---
@router.put("/{switch_id}/ports/{port_number}", response_model=SwitchPortInDB)
def update_switch_port(
    switch_id: int,
    port_number: int,
    payload: SwitchPortUpdate,
    db: Session = Depends(get_db),
    x_unit_id: int = Header(None),
    current_user = Depends(RequireRole(["ADMIN", "TECNICO"]))
):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    port = db.query(SwitchPort).filter(
        SwitchPort.switch_id == switch_id,
        SwitchPort.port_number == port_number,
        SwitchPort.unit_id == x_unit_id
    ).first()

    if not port:
        raise HTTPException(status_code=404, detail="Porta do switch não encontrada")

    prev_data = {
        "status": port.status,
        "vlan_id": port.vlan_id,
        "destination_location_id": port.destination_location_id,
        "connected_device_id": port.connected_device_id
    }

    # Inline Location Creation
    if payload.new_location_name and not payload.destination_location_id:
        loc = db.query(Location).filter(Location.name == payload.new_location_name, Location.unit_id == x_unit_id).first()
        if not loc:
            loc = Location(name=payload.new_location_name, unit_id=x_unit_id)
            db.add(loc)
            db.commit()
            db.refresh(loc)
        payload.destination_location_id = loc.id

    # Inline Device Creation
    if payload.new_device_name and not payload.connected_device_id:
        dev = db.query(Device).filter(Device.name == payload.new_device_name, Device.unit_id == x_unit_id).first()
        if not dev:
            dev = Device(
                name=payload.new_device_name,
                location_id=payload.destination_location_id,
                vlan_id=payload.vlan_id,
                unit_id=x_unit_id
            )
            db.add(dev)
            db.commit()
            db.refresh(dev)
        payload.connected_device_id = dev.id

    update_dict = payload.model_dump(exclude_unset=True, exclude={"new_location_name", "new_device_name"})

    for field, val in update_dict.items():
        setattr(port, field, val)

    # Auto status logic if status not explicitly changed or set to default
    if not payload.status or payload.status == port.status:
        if port.connected_device_id:
            port.status = PortStatus.CONNECTED.value
        elif port.connection_type == "Uplink":
            port.status = PortStatus.UPLINK.value
        elif port.destination_location_id or port.vlan_id:
            port.status = PortStatus.CONNECTED.value
        else:
            port.status = PortStatus.FREE.value

    db.commit()
    db.refresh(port)

    # Sync device location & VLAN if device attached
    if port.connected_device_id:
        dev = db.query(Device).filter(Device.id == port.connected_device_id).first()
        if dev:
            if port.destination_location_id:
                dev.location_id = port.destination_location_id
            if port.vlan_id:
                dev.vlan_id = port.vlan_id
            db.commit()

    log_audit(
        db,
        action="UPDATE",
        entity_type="SwitchPort",
        entity_id=port.id,
        entity_name=f"Switch {switch_id} - Porta {port_number}",
        previous_values=prev_data,
        new_values=update_dict
    )

    return enrich_port(port, db)
