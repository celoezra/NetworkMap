from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.models.domain import Rack, Switch, SwitchPort, Device, VLAN, Location, PortStatus
from app.schemas.domain import DashboardStats
from app.security.auth import RequireRole

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    x_unit_id: int = Header(None),
    current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))
):
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")

    total_racks = db.query(func.count(Rack.id)).filter(Rack.unit_id == x_unit_id).scalar() or 0
    total_switches = db.query(func.count(Switch.id)).filter(Switch.unit_id == x_unit_id).scalar() or 0
    total_ports = db.query(func.count(SwitchPort.id)).filter(SwitchPort.unit_id == x_unit_id).scalar() or 0
    
    used_ports = db.query(func.count(SwitchPort.id)).filter(
        SwitchPort.status != PortStatus.FREE.value,
        SwitchPort.unit_id == x_unit_id
    ).scalar() or 0
    
    free_ports = db.query(func.count(SwitchPort.id)).filter(
        SwitchPort.status == PortStatus.FREE.value,
        SwitchPort.unit_id == x_unit_id
    ).scalar() or 0
    
    total_devices = db.query(func.count(Device.id)).filter(Device.unit_id == x_unit_id).scalar() or 0
    total_vlans = db.query(func.count(VLAN.id)).filter(VLAN.unit_id == x_unit_id).scalar() or 0
    total_locations = db.query(func.count(Location.id)).filter(Location.unit_id == x_unit_id).scalar() or 0

    return DashboardStats(
        total_racks=total_racks,
        total_switches=total_switches,
        total_ports=total_ports,
        used_ports=used_ports,
        free_ports=free_ports,
        total_devices=total_devices,
        total_vlans=total_vlans,
        total_locations=total_locations
    )
