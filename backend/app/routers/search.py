from fastapi import APIRouter, Depends, Query, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, String, cast
from typing import List, Dict, Any
from app.database.connection import get_db
from app.models.domain import Device, Switch, SwitchPort, Rack, Location, VLAN, Connection
from app.schemas.domain import ConnectionCreate, ConnectionInDB
from app.services.audit import log_audit
from app.security.auth import RequireRole

router = APIRouter(prefix="/api/search", tags=["Global Search & Connections"])

@router.get("")
def global_search(
    q: str = Query(..., min_length=1, description="Termo de pesquisa"),
    db: Session = Depends(get_db),
    x_unit_id: int = Header(None),
    current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))
) -> Dict[str, Any]:
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    term = f"%{q}%"

    # 1. Search Devices
    devices = db.query(Device).filter(
        Device.unit_id == x_unit_id,
        or_(
            Device.name.ilike(term),
            Device.hostname.ilike(term),
            Device.ip_address.ilike(term),
            Device.mac_address.ilike(term),
            Device.asset_tag.ilike(term),
            Device.serial_number.ilike(term)
        )
    ).all()

    device_results = []
    for d in devices:
        port = db.query(SwitchPort).filter(SwitchPort.connected_device_id == d.id).first()
        sw = port.switch if port else None
        rack = sw.rack if sw else None
        vlan = d.vlan if d.vlan else (port.vlan if port else None)
        loc = d.location if d.location else (port.destination_location if port else None)

        device_results.append({
            "type": "device",
            "id": d.id,
            "name": d.name,
            "hostname": d.hostname,
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "device_type": d.device_type,
            "asset_tag": d.asset_tag,
            "serial_number": d.serial_number,
            "location_name": loc.name if loc else None,
            "rack_name": rack.name if rack else None,
            "switch_id": sw.id if sw else None,
            "switch_name": sw.name if sw else None,
            "port_number": port.port_number if port else None,
            "vlan_number": vlan.vlan_number if vlan else None,
            "vlan_name": vlan.name if vlan else None,
            "path_description": f"{d.name} → {loc.name if loc else 'Sem local'} → Porta {port.port_number if port else '?'} → {sw.name if sw else 'Sem Switch'} → {rack.name if rack else 'Sem Rack'}"
        })

    # 2. Search Switches
    switches = db.query(Switch).filter(
        Switch.unit_id == x_unit_id,
        or_(
            Switch.name.ilike(term),
            Switch.hostname.ilike(term),
            Switch.ip_address.ilike(term),
            Switch.mac_address.ilike(term)
        )
    ).all()

    switch_results = [{
        "type": "switch",
        "id": s.id,
        "name": s.name,
        "hostname": s.hostname,
        "ip_address": s.ip_address,
        "rack_name": s.rack.name if s.rack else None,
        "port_count": s.port_count
    } for s in switches]

    # 3. Search Racks
    racks = db.query(Rack).filter(
        Rack.unit_id == x_unit_id,
        or_(Rack.name.ilike(term), Rack.location_description.ilike(term))
    ).all()
    rack_results = [{"type": "rack", "id": r.id, "name": r.name, "location": r.location_description} for r in racks]

    # 4. Search Locations
    locations = db.query(Location).filter(
        Location.unit_id == x_unit_id,
        or_(Location.name.ilike(term), Location.sector.ilike(term))
    ).all()
    location_results = [{"type": "location", "id": l.id, "name": l.name, "sector": l.sector} for l in locations]

    # 5. Search VLANs
    vlans = db.query(VLAN).filter(
        VLAN.unit_id == x_unit_id,
        or_(VLAN.name.ilike(term), cast(VLAN.vlan_number, String).ilike(term))
    ).all()
    vlan_results = [{"type": "vlan", "id": v.id, "vlan_number": v.vlan_number, "name": v.name} for v in vlans]

    return {
        "query": q,
        "devices": device_results,
        "switches": switch_results,
        "racks": rack_results,
        "locations": location_results,
        "vlans": vlan_results,
        "total_matches": len(device_results) + len(switch_results) + len(rack_results) + len(location_results) + len(vlan_results)
    }

# --- UPLINK / SWITCH CONNECTIONS ENDPOINTS ---
connections_router = APIRouter(prefix="/api/connections", tags=["Connections"])

@connections_router.get("", response_model=List[ConnectionInDB])
def list_connections(db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    conns = db.query(Connection).filter(Connection.unit_id == x_unit_id).all()
    res = []
    for c in conns:
        res.append(ConnectionInDB(
            id=c.id,
            source_port_id=c.source_port_id,
            target_port_id=c.target_port_id,
            source_switch_name=c.source_port.switch.name if c.source_port and c.source_port.switch else None,
            source_port_number=c.source_port.port_number if c.source_port else None,
            target_switch_name=c.target_port.switch.name if c.target_port and c.target_port.switch else None,
            target_port_number=c.target_port.port_number if c.target_port else None,
            description=c.description,
            created_at=c.created_at
        ))
    return res

@connections_router.post("", response_model=ConnectionInDB, status_code=201)
def create_connection(payload: ConnectionCreate, db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO"]))):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    sp = db.query(SwitchPort).filter(SwitchPort.id == payload.source_port_id, SwitchPort.unit_id == x_unit_id).first()
    tp = db.query(SwitchPort).filter(SwitchPort.id == payload.target_port_id, SwitchPort.unit_id == x_unit_id).first()
    if not sp or not tp:
        raise HTTPException(status_code=404, detail="Uma ou ambas as portas especificadas não foram encontradas na unidade")

    conn = Connection(
        source_port_id=payload.source_port_id,
        target_port_id=payload.target_port_id,
        description=payload.description,
        unit_id=x_unit_id
    )
    db.add(conn)

    sp.connection_type = "Uplink"
    sp.status = "uplink"
    tp.connection_type = "Uplink"
    tp.status = "uplink"

    db.commit()
    db.refresh(conn)

    log_audit(
        db, action="CREATE", entity_type="Connection", entity_id=conn.id,
        entity_name=f"Uplink {sp.switch.name}:P{sp.port_number} <-> {tp.switch.name}:P{tp.port_number}"
    )

    return ConnectionInDB(
        id=conn.id,
        source_port_id=conn.source_port_id,
        target_port_id=conn.target_port_id,
        source_switch_name=sp.switch.name if sp.switch else None,
        source_port_number=sp.port_number,
        target_switch_name=tp.switch.name if tp.switch else None,
        target_port_number=tp.port_number,
        description=conn.description,
        created_at=conn.created_at
    )
