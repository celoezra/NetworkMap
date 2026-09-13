from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- RACK SCHEMAS ---
class RackBase(BaseModel):
    name: str
    location_description: str
    description: Optional[str] = None
    notes: Optional[str] = None

class RackCreate(RackBase):
    pass

class RackUpdate(BaseModel):
    name: Optional[str] = None
    location_description: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class RackInDB(RackBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- LOCATION SCHEMAS ---
class LocationBase(BaseModel):
    name: str
    sector: Optional[str] = None
    floor: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    floor: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class LocationInDB(LocationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- VLAN SCHEMAS ---
class VLANBase(BaseModel):
    vlan_number: int
    name: str
    description: Optional[str] = None
    subnet: Optional[str] = None
    gateway: Optional[str] = None

class VLANCreate(VLANBase):
    pass

class VLANUpdate(BaseModel):
    vlan_number: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    subnet: Optional[str] = None
    gateway: Optional[str] = None

class VLANInDB(VLANBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- DEVICE SCHEMAS ---
class DeviceBase(BaseModel):
    name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    device_type: str = "computador"
    location_id: Optional[int] = None
    vlan_id: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    asset_tag: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class DeviceCreate(DeviceBase):
    switch_id: Optional[int] = None
    port_id: Optional[int] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    device_type: Optional[str] = None
    location_id: Optional[int] = None
    vlan_id: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    asset_tag: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class DeviceInDB(DeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    location_name: Optional[str] = None
    vlan_name: Optional[str] = None
    connected_switch_id: Optional[int] = None
    connected_switch_name: Optional[str] = None
    connected_port_number: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

# --- SWITCH PORT SCHEMAS ---
class SwitchPortBase(BaseModel):
    port_number: int
    name: Optional[str] = None
    description: Optional[str] = None
    vlan_id: Optional[int] = None
    destination_location_id: Optional[int] = None
    connected_device_id: Optional[int] = None
    connection_type: str = "Access" # Access, Trunk, Uplink
    status: str = "free" # connected, free, uplink, network_device, issue
    notes: Optional[str] = None

class SwitchPortUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    vlan_id: Optional[int] = None
    destination_location_id: Optional[int] = None
    connected_device_id: Optional[int] = None
    connection_type: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    # Quick creation helpers
    new_location_name: Optional[str] = None
    new_device_name: Optional[str] = None

class SwitchPortInDB(SwitchPortBase):
    id: int
    switch_id: int
    vlan_number: Optional[int] = None
    vlan_name: Optional[str] = None
    destination_location_name: Optional[str] = None
    connected_device_name: Optional[str] = None
    connected_device_ip: Optional[str] = None
    connected_device_mac: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- SWITCH SCHEMAS ---
class SwitchBase(BaseModel):
    name: str
    hostname: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    port_count: int = 24
    rack_id: Optional[int] = None
    rack_position: Optional[str] = None
    notes: Optional[str] = None

class SwitchCreate(SwitchBase):
    pass

class SwitchUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    port_count: Optional[int] = None
    rack_id: Optional[int] = None
    rack_position: Optional[str] = None
    notes: Optional[str] = None

class SwitchInDB(SwitchBase):
    id: int
    rack_name: Optional[str] = None
    ports: List[SwitchPortInDB] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- CONNECTION / UPLINK SCHEMAS ---
class ConnectionCreate(BaseModel):
    source_port_id: int
    target_port_id: int
    description: Optional[str] = None

class ConnectionInDB(BaseModel):
    id: int
    source_port_id: int
    target_port_id: int
    source_switch_name: Optional[str] = None
    source_port_number: Optional[int] = None
    target_switch_name: Optional[str] = None
    target_port_number: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- DASHBOARD & AUDIT SCHEMAS ---
class DashboardStats(BaseModel):
    total_racks: int
    total_switches: int
    total_ports: int
    used_ports: int
    free_ports: int
    total_devices: int
    total_vlans: int
    total_locations: int

class AuditLogInDB(BaseModel):
    id: int
    timestamp: datetime
    user: str
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    previous_values: Optional[str] = None
    new_values: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
