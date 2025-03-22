from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
import json
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.services import user_service

security = HTTPBearer()

async def get_clerk_jwks():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.clerk.dev/v1/jwks")
        return response.json()

async def verify_token(token: str):
    try:
        # Extract kid from token header
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        if not kid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header")
        
        # Get JWKs from Clerk
        jwks = await get_clerk_jwks()
        
        # Find the key matching the kid
        key = None
        for jwk in jwks["keys"]:
            if jwk.get("kid") == kid:
                key = jwk
                break
        
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token key")
        
        # Convert JWK to PEM
        public_key = RSAAlgorithm.from_jwk(json.dumps(key))
        
        # Verify token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.CLERK_PUBLISHABLE_KEY
        )
        
        # Extract user ID from the subject claim
        clerk_id = payload.get("sub")
        
        if not clerk_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
        
        return clerk_id
    
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        clerk_id = await verify_token(credentials.credentials)
        user = user_service.get_user_by_clerk_id(db=db, clerk_id=clerk_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )