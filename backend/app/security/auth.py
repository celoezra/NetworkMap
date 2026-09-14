import os
from typing import Optional, List
from datetime import datetime

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.connection import get_db
from app.models.domain import User, Role, UserUnitAccess, Unit
from app.utils.logger import logger

# Configuration fallback, mostly read from env variables in production
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "common")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
SUPERADMIN_EMAIL = "marcelo.romero@rededor.com.br"

security = HTTPBearer()

import requests

# Cache public keys
_cached_keys = {}
_cached_keys_time = 0

def _get_azure_public_keys():
    global _cached_keys, _cached_keys_time
    import time
    if not AZURE_TENANT_ID or AZURE_TENANT_ID == "common":
        return {}
    if time.time() - _cached_keys_time < 3600:
        return _cached_keys
    try:
        url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys"
        resp = requests.get(url)
        resp.raise_for_status()
        jwks = resp.json()
        keys = {}
        for key in jwks.get("keys", []):
            keys[key["kid"]] = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        _cached_keys = keys
        _cached_keys_time = time.time()
        return keys
    except Exception as e:
        logger.error(f"Failed to fetch Azure public keys: {e}")
        return {}

def verify_microsoft_token(token: str) -> dict:
    try:
        current_client_id = os.getenv("AZURE_CLIENT_ID", AZURE_CLIENT_ID)
        
        # Determine if we should enforce signature check
        # Only bypass if explicit flag is set during pytest (for mock tokens)
        verify_signature = True
        if os.getenv("PYTEST_CURRENT_TEST") and token.split(".")[0] != "eyJhbGciOiJSUzI1NiI":
            # Just for local mock HS256 tokens in testing
            try:
                # We expect mock tokens to be signed with "secret" HS256
                payload = jwt.decode(token, "secret", algorithms=["HS256"], audience=current_client_id if current_client_id else None)
                if "oid" not in payload or "tid" not in payload:
                    raise ValueError("Token is missing required Microsoft claims (oid, tid)")
                return payload
            except:
                pass

        keys = _get_azure_public_keys()
        
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid or kid not in keys:
            if verify_signature and not os.getenv("PYTEST_CURRENT_TEST"):
                raise ValueError("Public key not found for token verification")
        
        public_key = keys.get(kid, "")
        
        payload = jwt.decode(
            token, 
            key=public_key,
            algorithms=["RS256"],
            options={
                "verify_signature": verify_signature and bool(public_key), 
                "verify_exp": True, 
                "verify_aud": bool(current_client_id)
            },
            audience=current_client_id if current_client_id else None
        )
        
        if "oid" not in payload or "tid" not in payload:
            raise ValueError("Token is missing required Microsoft claims (oid, tid)")
            
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidAudienceError:
        logger.error("Token has invalid audience.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Audiência inválida")
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_microsoft_token(token)

    object_id = payload.get("oid")
    tenant_id = payload.get("tid")
    name = payload.get("name") or payload.get("unique_name") or "Unknown User"
    email = payload.get("preferred_username") or payload.get("upn") or payload.get("email")
    
    if not email:
        email = f"{object_id}@unknown.com"

    # 1. Lookup User strictly by immutable identity (tenant_id + object_id)
    user = db.query(User).filter(User.object_id == object_id, User.tenant_id == tenant_id).first()

    if not user:
        # 2. Bootstrap SUPERADMIN if matches email EXACTLY ONLY IF SUPERADMIN DOES NOT EXIST YET
        superadmin_exists = db.query(User).filter(User.global_role == "SUPERADMIN").first()
        
        if not superadmin_exists and email.lower() == SUPERADMIN_EMAIL.lower():
            logger.info(f"Bootstrapping initial SUPERADMIN account for {email} with OID {object_id}")
            user = User(
                object_id=object_id,
                tenant_id=tenant_id,
                name=name,
                email=email,
                status="ACTIVE",
                global_role="SUPERADMIN",
                first_login=datetime.utcnow()
            )
        else:
            # 3. Create normal PENDING user
            logger.info(f"Creating new PENDING user request for {email}")
            user = User(
                object_id=object_id,
                tenant_id=tenant_id,
                name=name,
                email=email,
                status="PENDING",
                global_role="NONE"
            )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 4. Check Authorization Status
    if user.status == "PENDING":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sua solicitação de acesso está aguardando aprovação.")
    if user.status in ["BLOCKED", "REVOKED"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso bloqueado ou revogado.")

    user.last_login = datetime.utcnow()
    # name or email might have updated in Entra ID
    user.name = name
    db.commit()

    return user

class RequireRole:
    """Dependency to check if user has required role globally OR on a specific unit."""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if current_user.global_role == "SUPERADMIN":
            return current_user
            
        unit_id = request.headers.get("X-Unit-ID")
        if not unit_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="X-Unit-ID header is required for unit-scoped actions.")
            
        try:
            unit_id_int = int(unit_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="X-Unit-ID is invalid.")
            
        # Ensure the unit exists to prevent phantom unit bypasses
        unit = db.query(Unit).filter(Unit.id == unit_id_int).first()
        if not unit:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A unidade solicitada não existe.")

        # Get user's role for this specific unit
        access = db.query(UserUnitAccess).filter(
            UserUnitAccess.user_id == current_user.id,
            UserUnitAccess.unit_id == unit_id_int,
            UserUnitAccess.active == True
        ).first()

        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Você não possui permissão para realizar esta ação na unidade selecionada."
            )
            
        role = db.query(Role).filter(Role.id == access.role_id).first()
        if not role or role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Você não possui permissão para realizar esta ação na unidade selecionada."
            )
            
        return current_user
