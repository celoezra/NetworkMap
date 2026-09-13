import json
from sqlalchemy.orm import Session
from app.models.domain import AuditLog

def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int = None,
    entity_name: str = None,
    previous_values: dict = None,
    new_values: dict = None,
    user: str = "Técnico TI"
):
    """
    Utility to write audit trail entries into audit_logs table.
    """
    prev_str = json.dumps(previous_values, default=str, ensure_ascii=False) if previous_values else None
    new_str = json.dumps(new_values, default=str, ensure_ascii=False) if new_values else None

    entry = AuditLog(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        previous_values=prev_str,
        new_values=new_str
    )
    db.add(entry)
    db.commit()
    return entry
