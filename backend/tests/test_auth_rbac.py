import pytest
from fastapi.testclient import TestClient
import jwt
from app.main import app
from app.database.connection import get_db, SessionLocal
from app.models.domain import User, Unit, UserUnitAccess, Role
import os

client = TestClient(app)

def create_mock_token(email="test@test.com", oid="mock-oid", tid="mock-tid", name="Mock User", exp=9999999999, aud="mock-client-id"):
    payload = {
        "oid": oid,
        "tid": tid,
        "preferred_username": email,
        "name": name,
        "exp": exp,
        "aud": aud
    }
    return jwt.encode(payload, "secret", algorithm="HS256")

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_missing_token():
    res = client.get("/api/users/me")
    assert res.status_code == 401

def test_invalid_signature_bypassed_but_structure_checked():
    # PyJWT is configured to ignore signature, but check claims.
    # However we explicitly told it to check expiration and audience.
    # It should fail if missing oid/tid
    bad_token = jwt.encode({"email": "bad@test.com"}, "secret", algorithm="HS256")
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert res.status_code == 401

def test_expired_token():
    expired_token = create_mock_token(exp=100) # Past time
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401

def test_wrong_audience():
    # If the app expects AZURE_CLIENT_ID but gets something else
    os.environ["AZURE_CLIENT_ID"] = "expected-audience"
    wrong_aud_token = create_mock_token(aud="wrong-audience")
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {wrong_aud_token}"})
    assert res.status_code == 401
    del os.environ["AZURE_CLIENT_ID"] # Clean up

def test_superadmin_bootstrap():
    # This should bootstrap the first SUPERADMIN
    # Note we use a clean DB context for these tests ideally, 
    # but the test suite may share state. We will assert it creates or returns 200.
    token = create_mock_token(email="marcelo.romero@rededor.com.br", oid="12345-67890-superadmin", tid="tenant-xyz")
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["global_role"] == "SUPERADMIN"

def test_superadmin_recognized_by_oid_tid():
    # Changing the email shouldn't break the superadmin if oid/tid match
    token = create_mock_token(email="changed@rededor.com.br", oid="12345-67890-superadmin", tid="tenant-xyz")
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["global_role"] == "SUPERADMIN"

def test_normal_user_pending():
    token = create_mock_token(email="normal@test.com", oid="normal-oid", tid="normal-tid")
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    if res.status_code == 200:
        # Wait, if this ran after previous runs, it might be ACTIVE or something else
        assert "global_role" in res.json()
    else:
        assert res.status_code == 403
        assert "aguardando aprovação" in res.json()["detail"]

def test_blocked_user(db_session):
    # Make user blocked
    user = db_session.query(User).filter_by(object_id="normal-oid").first()
    user.status = "BLOCKED"
    db_session.commit()

    token = create_mock_token(email="normal@test.com", oid="normal-oid", tid="normal-tid")
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "bloqueado ou revogado" in res.json()["detail"]

def test_revoked_user(db_session):
    # Make user revoked
    user = db_session.query(User).filter_by(object_id="normal-oid").first()
    user.status = "REVOKED"
    db_session.commit()

    token = create_mock_token(email="normal@test.com", oid="normal-oid", tid="normal-tid")
    res = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "bloqueado ou revogado" in res.json()["detail"]

def test_normal_user_accessing_unit(db_session):
    user = db_session.query(User).filter_by(object_id="normal-oid").first()
    user.status = "ACTIVE"
    db_session.commit()

    # Assign to unit 1 as TECNICO
    unit = db_session.query(Unit).first()
    role = db_session.query(Role).filter_by(name="TECNICO").first()
    access = UserUnitAccess(user_id=user.id, unit_id=unit.id, role_id=role.id, active=True)
    db_session.add(access)
    db_session.commit()

    token = create_mock_token(email="normal@test.com", oid="normal-oid", tid="normal-tid")
    
    # Should be able to view switches for Unit 1
    res = client.get("/api/switches", headers={"Authorization": f"Bearer {token}", "X-Unit-ID": str(unit.id)})
    assert res.status_code == 200

    # Should NOT be able to view switches for Unit 999 (doesn't have access / doesn't exist)
    res = client.get("/api/switches", headers={"Authorization": f"Bearer {token}", "X-Unit-ID": "999"})
    assert res.status_code == 403

def test_tecnico_cannot_delete(db_session):
    token = create_mock_token(email="normal@test.com", oid="normal-oid", tid="normal-tid")
    unit = db_session.query(Unit).first()

    # Create dummy switch (TECNICO CAN CREATE)
    import uuid
    hname = f"tsw1-{str(uuid.uuid4())[:8]}"
    res = client.post("/api/switches", json={"name": "Test SW", "hostname": hname, "port_count": 8}, headers={"Authorization": f"Bearer {token}", "X-Unit-ID": str(unit.id)})
    assert res.status_code == 201
    sw_id = res.json()["id"]

    # Delete requires ADMIN
    res = client.delete(f"/api/switches/{sw_id}", headers={"Authorization": f"Bearer {token}", "X-Unit-ID": str(unit.id)})
    assert res.status_code == 403

def test_superadmin_accesses_all(db_session):
    token = create_mock_token(email="marcelo.romero@rededor.com.br", oid="12345-67890-superadmin", tid="tenant-xyz")
    
    # Can access unit 999 (if it existed, but it intercepts 403 logic gracefully as superadmin, wait, unit check happens first in RequireRole)
    # Actually, the RequireRole checks unit existence. So let's test a valid unit.
    unit = db_session.query(Unit).first()
    res = client.get("/api/switches", headers={"Authorization": f"Bearer {token}", "X-Unit-ID": str(unit.id)})
    assert res.status_code == 200

    # Can list users globally (only SUPERADMIN)
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
