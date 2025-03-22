from pydantic import BaseModel, UUID4
from typing import Optional, Dict, List, Any
from datetime import datetime

class HoneypotBase(BaseModel):
    name: str
    type: str
    ip_address: str
    port: str
    emulated_system: Optional[str] = None
    description: Optional[str] = None
    vulnerabilities: Optional[List[str]] = []

class HoneypotCreate(HoneypotBase):
    configuration: Optional[Dict[str, Any]] = {}

class HoneypotUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[str] = None
    status: Optional[str] = None
    emulated_system: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    vulnerabilities: Optional[List[str]] = None

class HoneypotInDBBase(HoneypotBase):
    id: UUID4
    status: str
    configuration: Dict[str, Any]
    user_id: UUID4
    attack_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        # orm_mode = True
        from_attributes = True

class Honeypot(HoneypotInDBBase):
    pass