from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID
from app.models.honeypot import Honeypot
from app.schemas.honeypot import HoneypotCreate, HoneypotUpdate
from app.services.honeypot_manager import deploy_honeypot_instance, update_honeypot_instance, remove_honeypot_instance

def create_honeypot(db: Session, honeypot_in: HoneypotCreate, user_id: UUID) -> Honeypot:
    """Create a new honeypot"""
    honeypot_data = honeypot_in.dict()
    db_honeypot = Honeypot(**honeypot_data, user_id=user_id)
    
    db.add(db_honeypot)
    db.commit()
    db.refresh(db_honeypot)
    return db_honeypot

def get_honeypots(
    db: Session, 
    user_id: UUID, 
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    type: Optional[str] = None
) -> List[Honeypot]:
    """Get all honeypots for a user with optional filters"""
    query = db.query(Honeypot).filter(Honeypot.user_id == user_id)
    
    if status:
        query = query.filter(Honeypot.status == status)
    
    if type:
        query = query.filter(Honeypot.type == type)
    
    return query.offset(skip).limit(limit).all()

def get_honeypot(db: Session, honeypot_id: UUID, user_id: UUID) -> Optional[Honeypot]:
    """Get a specific honeypot by ID"""
    return db.query(Honeypot).filter(
        Honeypot.id == honeypot_id,
        Honeypot.user_id == user_id
    ).options(joinedload(Honeypot.attacks)).first()

def update_honeypot(db: Session, honeypot: Honeypot, honeypot_in: HoneypotUpdate) -> Honeypot:
    """Update honeypot details"""
    update_data = honeypot_in.dict(exclude_unset=True)
    
    # Update honeypot in database
    for field, value in update_data.items():
        setattr(honeypot, field, value)
    
    db.add(honeypot)
    db.commit()
    db.refresh(honeypot)
    
    # If the honeypot is active, update the actual instance
    if honeypot.status == "active":
        update_honeypot_instance(honeypot)
    
    return honeypot

def delete_honeypot(db: Session, honeypot_id: UUID, user_id: UUID) -> bool:
    """Delete a honeypot"""
    honeypot = db.query(Honeypot).filter(
        Honeypot.id == honeypot_id,
        Honeypot.user_id == user_id
    ).first()
    
    if not honeypot:
        return False
    
    # If the honeypot is active, remove the actual instance
    if honeypot.status == "active":
        remove_honeypot_instance(honeypot)
    
    # Delete from database
    db.delete(honeypot)
    db.commit()
    return True

def deploy_honeypot(db: Session, honeypot_id: UUID, user_id: UUID) -> Optional[Honeypot]:
    """Deploy a honeypot"""
    honeypot = get_honeypot(db, honeypot_id, user_id)
    
    if not honeypot:
        return None
    
    # Call the honeypot manager to deploy the actual honeypot
    success = deploy_honeypot_instance(honeypot)
    
    if success:
        honeypot.status = "active"
        db.add(honeypot)
        db.commit()
        db.refresh(honeypot)
        return honeypot
    else:
        honeypot.status = "error"
        db.add(honeypot)
        db.commit()
        db.refresh(honeypot)
        return honeypot