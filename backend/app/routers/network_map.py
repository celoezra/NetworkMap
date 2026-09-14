from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database.connection import get_db
from app.models.domain import Rack, Switch, SwitchPort, Device, Location, VLAN, Connection
from app.security.auth import RequireRole

router = APIRouter(prefix="/api/network-map", tags=["Network Map Graph Data"])

@router.get("")
def get_network_map_graph(db: Session = Depends(get_db), x_unit_id: int = Header(None), current_user = Depends(RequireRole(["ADMIN", "TECNICO", "VISUALIZACAO"]))) -> Dict[str, Any]:
    if not x_unit_id:
        raise HTTPException(status_code=403, detail="X-Unit-ID header required")
    """
    Generates React Flow nodes and edges dynamically based on real network entities.
    Hierarchy:
    Rack -> Switch -> SwitchPort / VLAN / Location -> Device
    """
    nodes = []
    edges = []

    racks = db.query(Rack).filter(Rack.unit_id == x_unit_id).all()
    switches = db.query(Switch).filter(Switch.unit_id == x_unit_id).all()
    connections = db.query(Connection).filter(Connection.unit_id == x_unit_id).all()
    devices = db.query(Device).filter(Device.unit_id == x_unit_id).all()

    # Track positioning layout coordinates
    rack_x = 50
    rack_y = 50

    # 1. Racks Nodes
    for r in racks:
        r_node_id = f"rack_{r.id}"
        nodes.append({
            "id": r_node_id,
            "type": "rackNode",
            "data": {
                "label": r.name,
                "location": r.location_description,
                "description": r.description,
                "id": r.id
            },
            "position": {"x": rack_x, "y": rack_y}
        })
        
        # Position switches attached to this rack
        sw_y = rack_y + 120
        rack_switches = [s for s in switches if s.rack_id == r.id]
        for sw in rack_switches:
            sw_node_id = f"switch_{sw.id}"
            nodes.append({
                "id": sw_node_id,
                "type": "switchNode",
                "data": {
                    "label": sw.name,
                    "hostname": sw.hostname,
                    "ip": sw.ip_address,
                    "ports": sw.port_count,
                    "id": sw.id
                },
                "position": {"x": rack_x + 300, "y": sw_y}
            })
            
            # Edge Rack -> Switch
            edges.append({
                "id": f"edge_{r_node_id}_{sw_node_id}",
                "source": r_node_id,
                "target": sw_node_id,
                "animated": False,
                "label": "Instalado em",
                "style": {"stroke": "#64748b", "strokeWidth": 2}
            })

            # Switches connected ports to devices
            dev_y = sw_y
            active_ports = db.query(SwitchPort).filter(
                SwitchPort.switch_id == sw.id,
                SwitchPort.connected_device_id.isnot(None)
            ).all()

            for port in active_ports:
                dev = port.connected_device
                if dev:
                    dev_node_id = f"device_{dev.id}"
                    # Check if device node already added
                    if not any(n["id"] == dev_node_id for n in nodes):
                        loc_name = dev.location.name if dev.location else (port.destination_location.name if port.destination_location else "N/A")
                        vlan_num = dev.vlan.vlan_number if dev.vlan else (port.vlan.vlan_number if port.vlan else "N/A")
                        nodes.append({
                            "id": dev_node_id,
                            "type": "deviceNode",
                            "data": {
                                "label": dev.name,
                                "type": dev.device_type,
                                "ip": dev.ip_address,
                                "mac": dev.mac_address,
                                "location": loc_name,
                                "vlan": vlan_num,
                                "id": dev.id
                            },
                            "position": {"x": rack_x + 700, "y": dev_y}
                        })
                        dev_y += 100

                    # Edge Switch -> Device
                    edges.append({
                        "id": f"edge_port_{port.id}_{dev_node_id}",
                        "source": sw_node_id,
                        "target": dev_node_id,
                        "animated": True,
                        "label": f"Porta {port.port_number} (VLAN {port.vlan.vlan_number if port.vlan else '1'})",
                        "style": {"stroke": "#3b82f6", "strokeWidth": 2}
                    })

            sw_y += 220

        rack_x += 1100

    # 2. Switches without racks
    unassigned_switches = [s for s in switches if s.rack_id is None]
    unassigned_x = 50
    unassigned_y = rack_y + 600
    for sw in unassigned_switches:
        sw_node_id = f"switch_{sw.id}"
        nodes.append({
            "id": sw_node_id,
            "type": "switchNode",
            "data": {
                "label": sw.name,
                "hostname": sw.hostname,
                "ip": sw.ip_address,
                "ports": sw.port_count,
                "id": sw.id
            },
            "position": {"x": unassigned_x, "y": unassigned_y}
        })
        unassigned_x += 350

    # 3. Inter-switch Uplink Edges
    for c in connections:
        if c.source_port and c.target_port:
            s_sw_id = f"switch_{c.source_port.switch_id}"
            t_sw_id = f"switch_{c.target_port.switch_id}"
            edges.append({
                "id": f"uplink_{c.id}",
                "source": s_sw_id,
                "target": t_sw_id,
                "animated": True,
                "label": f"Uplink P{c.source_port.port_number} ↔ P{c.target_port.port_number}",
                "style": {"stroke": "#eab308", "strokeWidth": 3}
            })

    return {"nodes": nodes, "edges": edges}
