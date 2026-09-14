import os
import shutil
import tempfile
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlcipher3 import dbapi2 as sqlite3

from app.database.connection import get_db, DB_PATH
from app.models.domain import User, Unit, AuditLog, DatabaseMetadata
from app.security.auth import RequireRole
from app.security.key_manager import get_or_create_database_key

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

def check_db_validity_and_get_metadata(temp_db_path: str):
    db_key = get_or_create_database_key()
    safe_key = db_key.replace("'", "''")

    try:
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA key = '{safe_key}'")
        # Validate key works and schema exists
        cursor.execute("SELECT count(*) FROM sqlite_master")
        cursor.fetchone()
        
        # Read metadata
        cursor.execute("SELECT application_name, database_id, organization_id, schema_version FROM database_metadata LIMIT 1")
        row = cursor.fetchone()
        
        # Check standard objects existence to prove it is a networkmap db
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name IN ('racks', 'switches', 'devices')")
        tables_count = cursor.fetchone()[0]
        
        if tables_count < 3:
            raise Exception("Banco de dados não possui as tabelas necessárias do NetworkMap")
        
        conn.close()

        if row:
            return {
                "application_name": row[0],
                "database_id": row[1],
                "organization_id": row[2],
                "schema_version": row[3]
            }
        return {"application_name": "NetworkMap", "schema_version": 1} # Fallback for old ones

    except sqlite3.DatabaseError:
        raise HTTPException(status_code=400, detail="Chave do SQLCipher inválida ou arquivo corrompido")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/import")
def import_database(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["SUPERADMIN"]))
):
    """
    Importa e mescla os dados de um banco enviado. Cria uma nova unidade para abrigar esses dados.
    """
    if not file.filename.endswith('.db'):
        raise HTTPException(status_code=400, detail="Somente arquivos .db são suportados")

    import sys
    temp_dir = tempfile.mkdtemp()
    # Enforce restricted permissions for security on Unix
    if sys.platform != "win32":
        os.chmod(temp_dir, 0o700)
    
    # Safe path construction to prevent path traversal
    safe_filename = os.path.basename(file.filename)
    temp_path = os.path.join(temp_dir, safe_filename)

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    if sys.platform != "win32":
        os.chmod(temp_path, 0o600)

    try:
        metadata = check_db_validity_and_get_metadata(temp_path)
        
        if metadata.get('application_name') != 'NetworkMap':
             raise HTTPException(status_code=400, detail="O banco de dados não é uma base legítima do NetworkMap")

        # Check for duplicate imports using database_id
        db_id = metadata.get('database_id')
        if db_id:
            existing_unit = db.query(Unit).filter(Unit.description.like(f"%DB ID: {db_id}%")).first()
            if existing_unit:
                raise HTTPException(status_code=409, detail=f"Este banco de dados já foi importado (Unidade: {existing_unit.name})")

        # Backup current database before proceeding
        try:
            from app.routers.system import create_backup
            create_backup(db, current_user)
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Falha ao criar backup de segurança antes da importação: {e}")

        # Start explicit transaction context
        try:
            # Create a new unit for the imported data to avoid ID collision
            new_unit = Unit(
                name=f"Importado - {datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                description=f"Importado de arquivo: {file.filename}, DB ID: {db_id}",
                code=str(uuid.uuid4())[:8]
            )
            db.add(new_unit)
            db.flush() # Flush to get new_unit.id

            db_key = get_or_create_database_key()
            safe_key = db_key.replace("'", "''")

            conn = sqlite3.connect(temp_path)
            try:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA key = '{safe_key}'")
                
                # We need to map old IDs to new IDs during import to preserve relationships
                id_maps = {
                    'racks': {},
                    'switches': {},
                    'locations': {},
                    'vlans': {},
                    'devices': {},
                    'ports': {}
                }
                
                # 1. Racks
                cursor.execute("SELECT id, uuid, name, location_description, description, notes, created_at, updated_at FROM racks")
                for row in cursor.fetchall():
                    # Check if UUID already exists to avoid duplicates
                    existing = db.execute(text("SELECT id FROM racks WHERE uuid = :uuid"), {"uuid": row[1]}).first()
                    if existing:
                         id_maps['racks'][row[0]] = existing[0]
                    else:
                         res = db.execute(
                            text("INSERT INTO racks (uuid, unit_id, name, location_description, description, notes, created_at, updated_at) VALUES (:uuid, :unit_id, :name, :location_description, :description, :notes, :created_at, :updated_at) RETURNING id"),
                            {"uuid": row[1], "unit_id": new_unit.id, "name": row[2], "location_description": row[3], "description": row[4], "notes": row[5], "created_at": row[6], "updated_at": row[7]}
                         )
                         id_maps['racks'][row[0]] = res.scalar()

                # 2. Locations
                cursor.execute("SELECT id, uuid, name, sector, floor, description, notes, created_at, updated_at FROM locations")
                for row in cursor.fetchall():
                    existing = db.execute(text("SELECT id FROM locations WHERE uuid = :uuid"), {"uuid": row[1]}).first()
                    if existing:
                         id_maps['locations'][row[0]] = existing[0]
                    else:
                         res = db.execute(
                            text("INSERT INTO locations (uuid, unit_id, name, sector, floor, description, notes, created_at, updated_at) VALUES (:uuid, :unit_id, :name, :sector, :floor, :description, :notes, :created_at, :updated_at) RETURNING id"),
                            {"uuid": row[1], "unit_id": new_unit.id, "name": row[2], "sector": row[3], "floor": row[4], "description": row[5], "notes": row[6], "created_at": row[7], "updated_at": row[8]}
                         )
                         id_maps['locations'][row[0]] = res.scalar()

                # 3. VLANs
                cursor.execute("SELECT id, uuid, vlan_number, name, description, subnet, gateway, created_at, updated_at FROM vlans")
                for row in cursor.fetchall():
                    existing = db.execute(text("SELECT id FROM vlans WHERE uuid = :uuid"), {"uuid": row[1]}).first()
                    if existing:
                         id_maps['vlans'][row[0]] = existing[0]
                    else:
                         res = db.execute(
                            text("INSERT INTO vlans (uuid, unit_id, vlan_number, name, description, subnet, gateway, created_at, updated_at) VALUES (:uuid, :unit_id, :vlan_number, :name, :description, :subnet, :gateway, :created_at, :updated_at) RETURNING id"),
                            {"uuid": row[1], "unit_id": new_unit.id, "vlan_number": row[2], "name": row[3], "description": row[4], "subnet": row[5], "gateway": row[6], "created_at": row[7], "updated_at": row[8]}
                         )
                         id_maps['vlans'][row[0]] = res.scalar()
                
                # 4. Switches
                cursor.execute("SELECT id, uuid, name, hostname, manufacturer, model, ip_address, mac_address, port_count, rack_id, rack_position, notes, created_at, updated_at FROM switches")
                for row in cursor.fetchall():
                    existing = db.execute(text("SELECT id FROM switches WHERE uuid = :uuid"), {"uuid": row[1]}).first()
                    if existing:
                         id_maps['switches'][row[0]] = existing[0]
                    else:
                         mapped_rack_id = id_maps['racks'].get(row[9]) if row[9] else None
                         res = db.execute(
                            text("INSERT INTO switches (uuid, unit_id, name, hostname, manufacturer, model, ip_address, mac_address, port_count, rack_id, rack_position, notes, created_at, updated_at) VALUES (:uuid, :unit_id, :name, :hostname, :manufacturer, :model, :ip_address, :mac_address, :port_count, :rack_id, :rack_position, :notes, :created_at, :updated_at) RETURNING id"),
                            {"uuid": row[1], "unit_id": new_unit.id, "name": row[2], "hostname": row[3], "manufacturer": row[4], "model": row[5], "ip_address": row[6], "mac_address": row[7], "port_count": row[8], "rack_id": mapped_rack_id, "rack_position": row[10], "notes": row[11], "created_at": row[12], "updated_at": row[13]}
                         )
                         id_maps['switches'][row[0]] = res.scalar()

                # 5. Devices
                cursor.execute("SELECT id, uuid, name, hostname, ip_address, mac_address, device_type, location_id, vlan_id, manufacturer, model, asset_tag, serial_number, description, notes, created_at, updated_at FROM devices")
                for row in cursor.fetchall():
                    existing = db.execute(text("SELECT id FROM devices WHERE uuid = :uuid"), {"uuid": row[1]}).first()
                    if existing:
                         id_maps['devices'][row[0]] = existing[0]
                    else:
                         mapped_loc = id_maps['locations'].get(row[7]) if row[7] else None
                         mapped_vlan = id_maps['vlans'].get(row[8]) if row[8] else None
                         res = db.execute(
                            text("INSERT INTO devices (uuid, unit_id, name, hostname, ip_address, mac_address, device_type, location_id, vlan_id, manufacturer, model, asset_tag, serial_number, description, notes, created_at, updated_at) VALUES (:uuid, :unit_id, :name, :hostname, :ip_address, :mac_address, :device_type, :location_id, :vlan_id, :manufacturer, :model, :asset_tag, :serial_number, :description, :notes, :created_at, :updated_at) RETURNING id"),
                            {"uuid": row[1], "unit_id": new_unit.id, "name": row[2], "hostname": row[3], "ip_address": row[4], "mac_address": row[5], "device_type": row[6], "location_id": mapped_loc, "vlan_id": mapped_vlan, "manufacturer": row[9], "model": row[10], "asset_tag": row[11], "serial_number": row[12], "description": row[13], "notes": row[14], "created_at": row[15], "updated_at": row[16]}
                         )
                         id_maps['devices'][row[0]] = res.scalar()

                # 6. Switch Ports
                cursor.execute("SELECT id, uuid, switch_id, port_number, name, description, vlan_id, destination_location_id, connected_device_id, connection_type, status, notes, created_at, updated_at FROM switch_ports")
                for row in cursor.fetchall():
                    existing = db.execute(text("SELECT id FROM switch_ports WHERE uuid = :uuid"), {"uuid": row[1]}).first()
                    if existing:
                         id_maps['ports'][row[0]] = existing[0]
                    else:
                         mapped_sw = id_maps['switches'].get(row[2])
                         mapped_vlan = id_maps['vlans'].get(row[6]) if row[6] else None
                         mapped_loc = id_maps['locations'].get(row[7]) if row[7] else None
                         mapped_dev = id_maps['devices'].get(row[8]) if row[8] else None
                         if mapped_sw: # Must have switch
                             res = db.execute(
                                text("INSERT INTO switch_ports (uuid, unit_id, switch_id, port_number, name, description, vlan_id, destination_location_id, connected_device_id, connection_type, status, notes, created_at, updated_at) VALUES (:uuid, :unit_id, :switch_id, :port_number, :name, :description, :vlan_id, :destination_location_id, :connected_device_id, :connection_type, :status, :notes, :created_at, :updated_at) RETURNING id"),
                                {"uuid": row[1], "unit_id": new_unit.id, "switch_id": mapped_sw, "port_number": row[3], "name": row[4], "description": row[5], "vlan_id": mapped_vlan, "destination_location_id": mapped_loc, "connected_device_id": mapped_dev, "connection_type": row[9], "status": row[10], "notes": row[11], "created_at": row[12], "updated_at": row[13]}
                             )
                             id_maps['ports'][row[0]] = res.scalar()
                
                # 7. Connections
                cursor.execute("SELECT id, uuid, source_port_id, target_port_id, description, created_at FROM connections")
                for row in cursor.fetchall():
                    existing = db.execute(text("SELECT id FROM connections WHERE uuid = :uuid"), {"uuid": row[1]}).first()
                    if not existing:
                         mapped_sp = id_maps['ports'].get(row[2])
                         mapped_tp = id_maps['ports'].get(row[3])
                         if mapped_sp and mapped_tp:
                             db.execute(
                                text("INSERT INTO connections (uuid, unit_id, source_port_id, target_port_id, description, created_at) VALUES (:uuid, :unit_id, :source_port_id, :target_port_id, :description, :created_at)"),
                                {"uuid": row[1], "unit_id": new_unit.id, "source_port_id": mapped_sp, "target_port_id": mapped_tp, "description": row[4], "created_at": row[5]}
                             )

                db.commit()

                audit = AuditLog(
                    actor_user_id=current_user.id,
                    action="DATABASE_IMPORTED",
                    entity_type="Database",
                    entity_name=file.filename,
                    new_values=f"Importado como Unidade ID {new_unit.id}"
                )
                db.add(audit)
                db.commit()

            finally:
                conn.close()

            return {
                "message": "Banco validado e estrutural base importada com sucesso",
                "metadata": metadata,
                "new_unit_id": new_unit.id
            }

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erro durante a importação. Rollback executado. Detalhes: {e}")

    finally:
        if os.path.exists(temp_path):
             # Securely delete the plaintext key file fallback/DB
             try:
                 os.remove(temp_path)
             except:
                 pass
        shutil.rmtree(temp_dir, ignore_errors=True)
