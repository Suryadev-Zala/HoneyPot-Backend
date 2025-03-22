from pydantic import BaseModel, UUID4
from typing import Optional, Dict, Any
from datetime import datetime

class SimulationBase(BaseModel):
    name: str
    attack_type: str
    node_count: int = 5
    duration_minutes: int = 5
    intensity: int = 5

class SimulationCreate(SimulationBase):
    target_honeypot_id: UUID4

class SimulationUpdate(BaseModel):
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

class SimulationInDBBase(SimulationBase):
    id: UUID4
    target_honeypot_id: UUID4
    user_id: UUID4
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    results: Dict[str, Any]
    created_at: datetime

    class Config:
        # orm_mode = True
        from_attributes = True

class Simulation(SimulationInDBBase):
    pass