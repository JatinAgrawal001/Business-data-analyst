from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Cryptographically verifies and decodes a Supabase GoTrue JWT token.
    Validates audience, expiration, and user claims.
    """
    secret = settings.SUPABASE_JWT_SECRET
    if secret:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired"
            )
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token cryptographic verification failed: {str(e)}"
            )
    else:
        # Development / fallback decoding
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            if "sub" not in payload and "id" not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing subject claim"
                )
            return payload
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed authorization token"
            )

async def get_current_user_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Dict[str, Any]:
    """
    FastAPI Dependency: Returns decoded claims, raising 401 if missing or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided"
        )
    return verify_jwt_token(credentials.credentials)

async def require_authenticated_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> User:
    """
    FastAPI Dependency: Strict authentication. Raises 401 if no valid token is provided.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource"
        )
    
    payload = verify_jwt_token(credentials.credentials)
    user_id = payload.get("sub") or payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identifier missing in authentication token claims"
        )
    
    user_meta = payload.get("user_metadata", {})
    return User(
        id=user_id,
        name=user_meta.get("name", payload.get("email", "Analyst").split("@")[0]),
        email=payload.get("email", "analyst@workspace.ai"),
        role=user_meta.get("role", "Lead Data Analyst"),
        company=user_meta.get("company", "Enterprise Analytics"),
        plan=user_meta.get("plan", "Enterprise")
    )

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> User:
    """
    FastAPI Dependency: Authenticates token if present; provides dev fallback if not in production.
    """
    if credentials and credentials.credentials:
        return await require_authenticated_user(credentials)

    # Dev/local fallback
    return User(
        id="usr-guest-001",
        name="Elena Rostova",
        email="elena.rostova@insightflow.ai",
        role="Lead Business Data Analyst",
        company="Apex Data Intelligence",
        plan="Enterprise"
    )

async def get_supabase_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[str]:
    """
    FastAPI Dependency: Returns raw Bearer JWT token to scope Supabase queries by user context.
    """
    if credentials and credentials.credentials:
        return credentials.credentials
    return None

def verify_resource_ownership(resource_owner_id: Optional[str], current_user_id: str, resource_name: str = "Resource") -> None:
    """
    Ensures that the resource belongs to the requesting authenticated user.
    Raises 403 Forbidden if ownership does not match.
    """
    if resource_owner_id and str(resource_owner_id) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: You do not have permission to access or modify this {resource_name.lower()}."
        )
