from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
import hmac
import hashlib
import time
from app.core.config import settings
from app.core.database import get_db
from app.schemas import user as user_schemas
from app.services import user_service
from app.api.dependencies import get_current_user

router = APIRouter()

def verify_clerk_webhook(signature: str, timestamp: str, body: bytes):
    if not settings.CLERK_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Webhook secret not configured")
    
    # Verify that the timestamp is not too old
    try:
        timestamp_int = int(timestamp)
        current_time = int(time.time())
        if current_time - timestamp_int > 300:  # 5 minutes
            return False
    except ValueError:
        return False
    
    # Compute expected signature
    secret = settings.CLERK_WEBHOOK_SECRET.encode('utf-8')
    message = timestamp.encode('utf-8') + b'.' + body
    expected_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def clerk_webhook(
    request: Request,
    svix_id: str = Header(None),
    svix_timestamp: str = Header(None),
    svix_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """Handle Clerk webhooks for user management"""
    if not (svix_id and svix_timestamp and svix_signature):
        raise HTTPException(status_code=400, detail="Missing Svix headers")
    
    body = await request.body()
    if not verify_clerk_webhook(svix_signature, svix_timestamp, body):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    payload = await request.json()
    
    event_type = payload.get("type")
    
    if event_type == "user.created":
        user_data = payload.get("data", {})
        email_addresses = user_data.get("email_addresses", [])
        
        if not email_addresses:
            return {"status": "skipped", "reason": "No email address found"}
        
        email = email_addresses[0].get("email_address")
        
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or None
        clerk_id = user_data.get("id")
        
        if not clerk_id:
            return {"status": "error", "reason": "No Clerk ID found"}
        
        # Check if user already exists
        existing_user = user_service.get_user_by_clerk_id(db, clerk_id)
        if existing_user:
            return {"status": "skipped", "reason": "User already exists"}
        
        user_in = user_schemas.UserCreate(
            email=email,
            full_name=full_name,
            clerk_id=clerk_id
        )
        user_service.create_user(db=db, user_in=user_in)
        
        return {"status": "success", "message": "User created"}
    
    elif event_type == "user.updated":
        user_data = payload.get("data", {})
        clerk_id = user_data.get("id")
        
        if not clerk_id:
            return {"status": "error", "reason": "No Clerk ID found"}
        
        existing_user = user_service.get_user_by_clerk_id(db, clerk_id)
        if not existing_user:
            return {"status": "error", "reason": "User not found"}
        
        email_addresses = user_data.get("email_addresses", [])
        email = email_addresses[0].get("email_address") if email_addresses else None
        
        first_name = user_data.get("first_name")
        last_name = user_data.get("last_name")
        full_name = f"{first_name or ''} {last_name or ''}".strip() or None
        
        user_update = user_schemas.UserUpdate(
            email=email,
            full_name=full_name
        )
        
        user_service.update_user(db, existing_user, user_update)
        return {"status": "success", "message": "User updated"}
    
    return {"status": "ignored", "event": event_type}

@router.get("/me", response_model=user_schemas.User)
async def get_current_user_endpoint(
    current_user: user_schemas.User = Depends(get_current_user)
):
    """Get the current user"""
    return current_user