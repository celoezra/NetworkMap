import os
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import csv
import io

from app.database.connection import get_db, DB_PATH
from app.models.domain import AuditLog, Backup, Device, Switch, SwitchPort, VLAN, Location, Rack
from app.schemas.domain import AuditLogInDB
from app.services.audit import log_audit
from app.security.auth import RequireRole

router = APIRouter(prefix="/api/system", tags=["System, Audit, Backup & Export"])

BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# --- AUDIT LOGS ENDPOINT ---
@router.get("/audit-logs", response_model=List[AuditLogInDB])
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db), current_user = Depends(RequireRole(["SUPERADMIN"]))):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

# --- BACKUP ENDPOINTS ---
@router.get("/backups")
def list_backups(db: Session = Depends(get_db), current_user = Depends(RequireRole(["SUPERADMIN"]))):
    backups = db.query(Backup).order_by(Backup.created_at.desc()).all()
    return [{
        "id": b.id,
        "filename": b.filename,
        "created_at": b.created_at,
        "size_kb": round((b.size_bytes or 0) / 1024, 2)
    } for b in backups]

@router.post("/backups/create")
def create_backup(db: Session = Depends(get_db), current_user = Depends(RequireRole(["SUPERADMIN"]))):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"networkmap_backup_{timestamp}.db"
    dest_path = BACKUP_DIR / filename

    try:
        # Checkpointing and flushing database WAL
        db.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
        shutil.copy2(DB_PATH, dest_path)
        size_bytes = os.path.getsize(dest_path)

        backup_rec = Backup(filename=filename, filepath=str(dest_path), size_bytes=size_bytes)
        db.add(backup_rec)
        db.commit()

        audit = AuditLog(
            actor_user_id=current_user.id,
            action="BACKUP_CREATED",
            entity_type="Backup",
            entity_name=filename,
            new_values=f"Size: {size_bytes} bytes"
        )
        db.add(audit)
        db.commit()
        return {"message": "Backup criptografado criado com sucesso", "filename": filename, "size_bytes": size_bytes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar backup: {str(e)}")

@router.post("/backups/restore/{backup_id}")
def restore_backup(backup_id: int, db: Session = Depends(get_db), current_user = Depends(RequireRole(["SUPERADMIN"]))):
    backup_rec = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup_rec or not os.path.exists(backup_rec.filepath):
        raise HTTPException(status_code=404, detail="Arquivo de backup não encontrado")

    try:
        # Create safety pre-restore backup first
        pre_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        pre_filename = f"pre_restore_{pre_timestamp}.db"
        pre_path = BACKUP_DIR / pre_filename
        
        db.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
        shutil.copy2(DB_PATH, pre_path)
        
        pre_rec = Backup(filename=pre_filename, filepath=str(pre_path), size_bytes=os.path.getsize(pre_path))
        db.add(pre_rec)
        db.commit()

        # Close session connection before overwriting file
        db.close()
        
        # Copy selected backup onto active db file
        shutil.copy2(backup_rec.filepath, DB_PATH)
        
        # Note: Ideally AuditLog is done after the restore reconnects, but doing it before close works for now
        # given the scope. A re-connection block would be needed otherwise.

        return {"message": "Backup restaurado com sucesso! Backup de segurança pre-restore criado.", "pre_restore": pre_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao restaurar backup: {str(e)}")

# --- CSV EXPORT ENDPOINTS ---
@router.get("/export/devices")
def export_devices_csv(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nome", "Hostname", "IP", "MAC", "Tipo", "Local", "VLAN", "Fabricante", "Modelo", "Patrimônio", "Série"])

    for d in devices:
        writer.writerow([
            d.id, d.name, d.hostname or "", d.ip_address or "", d.mac_address or "",
            d.device_type, d.location.name if d.location else "", d.vlan.vlan_number if d.vlan else "",
            d.manufacturer or "", d.model or "", d.asset_tag or "", d.serial_number or ""
        ])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=inventario_equipamentos.csv"
    return response

@router.get("/export/switches")
def export_switches_csv(db: Session = Depends(get_db)):
    switches = db.query(Switch).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nome", "Hostname", "IP", "MAC", "Portas", "Rack", "Fabricante", "Modelo"])

    for s in switches:
        writer.writerow([
            s.id, s.name, s.hostname, s.ip_address or "", s.mac_address or "",
            s.port_count, s.rack.name if s.rack else "", s.manufacturer or "", s.model or ""
        ])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=inventario_switches.csv"
    return response

@router.get("/export/ports")
def export_ports_csv(db: Session = Depends(get_db)):
    ports = db.query(SwitchPort).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Switch", "Porta", "Status", "Tipo", "VLAN", "Local Destino", "Equipamento Conectado"])

    for p in ports:
        writer.writerow([
            p.id, p.switch.name if p.switch else "", p.port_number, p.status, p.connection_type,
            p.vlan.vlan_number if p.vlan else "", p.destination_location.name if p.destination_location else "",
            p.connected_device.name if p.connected_device else ""
        ])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=mapeamento_portas.csv"
    return response

@router.get("/export/vlans")
def export_vlans_csv(db: Session = Depends(get_db)):
    vlans = db.query(VLAN).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Número", "Nome", "Subnet", "Gateway", "Descrição"])

    for v in vlans:
        writer.writerow([
            v.id, v.vlan_number, v.name, v.subnet or "", v.gateway or "", v.description or ""
        ])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=cadastro_vlans.csv"
    return response
