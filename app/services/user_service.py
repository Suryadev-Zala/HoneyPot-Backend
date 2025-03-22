from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

def create_user(db: Session, user_in: UserCreate) -> User:
    """Create a new user"""
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        clerk_id=user_in.clerk_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str) -> User:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_clerk_id(db: Session, clerk_id: str) -> User:
    """Get a user by Clerk ID"""
    return db.query(User).filter(User.clerk_id == clerk_id).first()

def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    """Update user details"""
    update_data = user_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: UUID) -> None:
    """Delete a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()