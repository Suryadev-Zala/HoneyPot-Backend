from pydantic import BaseModel, UUID4
from typing import Optional, Dict, Any
from datetime import datetime

class AttackBase(BaseModel):
    source_ip: str
    attack_type: str
    severity: str
    details: Dict[str, Any]
    is_simulated: bool = False

class AttackCreate(AttackBase):
    honeypot_id: UUID4
    simulation_id: Optional[UUID4] = None

class AttackInDBBase(AttackBase):
    id: UUID4
    honeypot_id: UUID4
    simulation_id: Optional[UUID4] = None
    timestamp: datetime

    class Config:
        # orm_mode = True
        from_attributes = True

class Attack(AttackInDBBase):
    pass