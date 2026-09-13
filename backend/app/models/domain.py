from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum
)
from sqlalchemy.orm import relationship
import enum
from app.database.connection import Base

class PortStatus(str, enum.Enum):
    CONNECTED = "connected"      # Verde
    FREE = "free"                # Cinza
    UPLINK = "uplink"            # Amarelo
    NETWORK_DEVICE = "network_device" # Azul
    ISSUE = "issue"              # Vermelho

class DeviceType(str, enum.Enum):
    COMPUTER = "computador"
    NOTEBOOK = "notebook"
    PRINTER = "impressora"
    ACCESS_POINT = "access_point"
    SERVER = "servidor"
    CAMERA = "camera"
    IP_PHONE = "telefone_ip"
    PANEL = "painel"
    ROUTER = "roteador"
    SWITCH = "switch"
    FIREWALL = "firewall"
    MEDICAL = "equipamento_medico"
    GENERIC = "equipamento_generico"

class Rack(Base):
    __tablename__ = "racks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    location_description = Column(String(200), nullable=False) # e.g. Sala de TI
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    switches = relationship("Switch", back_populates="rack", cascade="all, delete-orphan")

class Switch(Base):
    __tablename__ = "switches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    hostname = Column(String(100), nullable=False, unique=True, index=True)
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    mac_address = Column(String(17), nullable=True, index=True)
    port_count = Column(Integer, nullable=False, default=24)
    rack_id = Column(Integer, ForeignKey("racks.id", ondelete="RESTRICT"), nullable=True)
    rack_position = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rack = relationship("Rack", back_populates="switches")
    ports = relationship("SwitchPort", back_populates="switch", cascade="all, delete-orphan", order_by="SwitchPort.port_number")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True) # e.g., Consultório 05
    sector = Column(String(100), nullable=True)                          # e.g., Ambulatório
    floor = Column(String(50), nullable=True)                           # e.g., 2º Andar
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    devices = relationship("Device", back_populates="location")
    ports = relationship("SwitchPort", back_populates="destination_location")

class VLAN(Base):
    __tablename__ = "vlans"

    id = Column(Integer, primary_key=True, index=True) # Used as VLAN ID (e.g., 10, 20)
    vlan_number = Column(Integer, nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    subnet = Column(String(50), nullable=True)
    gateway = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ports = relationship("SwitchPort", back_populates="vlan")
    devices = relationship("Device", back_populates="vlan")

class SwitchPort(Base):
    __tablename__ = "switch_ports"

    id = Column(Integer, primary_key=True, index=True)
    switch_id = Column(Integer, ForeignKey("switches.id", ondelete="CASCADE"), nullable=False)
    port_number = Column(Integer, nullable=False) # 1, 2, ..., N
    name = Column(String(100), nullable=True)     # Optional label
    description = Column(Text, nullable=True)
    
    vlan_id = Column(Integer, ForeignKey("vlans.id", ondelete="SET NULL"), nullable=True)
    destination_location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    connected_device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    
    connection_type = Column(String(50), default="Access") # Access, Trunk, Uplink
    status = Column(String(20), default=PortStatus.FREE.value) # connected, free, uplink, network_device, issue
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    switch = relationship("Switch", back_populates="ports")
    vlan = relationship("VLAN", back_populates="ports")
    destination_location = relationship("Location", back_populates="ports")
    connected_device = relationship("Device", back_populates="connected_ports", foreign_keys=[connected_device_id])

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    hostname = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    mac_address = Column(String(17), nullable=True, index=True)
    device_type = Column(String(50), default=DeviceType.COMPUTER.value)
    
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    vlan_id = Column(Integer, ForeignKey("vlans.id", ondelete="SET NULL"), nullable=True)
    
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    asset_tag = Column(String(100), nullable=True, index=True) # Patrimônio
    serial_number = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    location = relationship("Location", back_populates="devices")
    vlan = relationship("VLAN", back_populates="devices")
    connected_ports = relationship("SwitchPort", back_populates="connected_device", foreign_keys="[SwitchPort.connected_device_id]")

class Connection(Base):
    """Switch to Switch Uplink or Inter-device Connection"""
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    source_port_id = Column(Integer, ForeignKey("switch_ports.id", ondelete="CASCADE"), nullable=False, unique=True)
    target_port_id = Column(Integer, ForeignKey("switch_ports.id", ondelete="CASCADE"), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_port = relationship("SwitchPort", foreign_keys=[source_port_id])
    target_port = relationship("SwitchPort", foreign_keys=[target_port_id])

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user = Column(String(100), default="Técnico TI")
    action = Column(String(50), nullable=False) # CREATE, UPDATE, DELETE, RESTORE
    entity_type = Column(String(50), nullable=False) # Rack, Switch, Port, Location, etc.
    entity_id = Column(Integer, nullable=True)
    entity_name = Column(String(100), nullable=True)
    previous_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)

class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(200), nullable=False)
    filepath = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    size_bytes = Column(Integer, nullable=True)
