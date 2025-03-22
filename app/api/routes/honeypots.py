from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import honeypot as honeypot_schemas
from app.services import honeypot_service
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=honeypot_schemas.Honeypot, status_code=status.HTTP_201_CREATED)
def create_honeypot(
    honeypot_in: honeypot_schemas.HoneypotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new honeypot"""
    return honeypot_service.create_honeypot(db=db, honeypot_in=honeypot_in, user_id=current_user.id)

@router.get("/", response_model=List[honeypot_schemas.Honeypot])
def get_honeypots(
    status: Optional[str] = None,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all honeypots for the current user"""
    return honeypot_service.get_honeypots(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit, 
        status=status,
        type=type
    )

@router.get("/{honeypot_id}", response_model=honeypot_schemas.Honeypot)
def get_honeypot(
    honeypot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific honeypot"""
    honeypot = honeypot_service.get_honeypot(db=db, honeypot_id=honeypot_id, user_id=current_user.id)
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    return honeypot

@router.put("/{honeypot_id}", response_model=honeypot_schemas.Honeypot)
def update_honeypot(
    honeypot_id: UUID,
    honeypot_in: honeypot_schemas.HoneypotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a honeypot"""
    honeypot = honeypot_service.get_honeypot(db=db, honeypot_id=honeypot_id, user_id=current_user.id)
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    
    return honeypot_service.update_honeypot(db=db, honeypot=honeypot, honeypot_in=honeypot_in)

@router.delete("/{honeypot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_honeypot(
    honeypot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a honeypot"""
    success = honeypot_service.delete_honeypot(db=db, honeypot_id=honeypot_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Honeypot not found")

@router.post("/{honeypot_id}/deploy", response_model=honeypot_schemas.Honeypot)
def deploy_honeypot(
    honeypot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deploy a honeypot"""
    honeypot = honeypot_service.deploy_honeypot(db=db, honeypot_id=honeypot_id, user_id=current_user.id)
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    
    if honeypot.status == "error":
        raise HTTPException(status_code=500, detail="Failed to deploy honeypot")
    
    return honeypot