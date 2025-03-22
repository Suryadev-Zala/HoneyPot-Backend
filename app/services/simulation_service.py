from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.models.simulation import Simulation
from app.schemas.simulation import SimulationCreate, SimulationUpdate
from app.services.attack_simulator import start_simulation_background_task

def create_simulation(db: Session, simulation_in: SimulationCreate, user_id: UUID) -> Simulation:
    """Create a new simulation"""
    simulation_data = simulation_in.dict()
    db_simulation = Simulation(**simulation_data, user_id=user_id)
    
    db.add(db_simulation)
    db.commit()
    db.refresh(db_simulation)
    return db_simulation

def get_simulations(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Simulation]:
    """Get all simulations for a user"""
    return db.query(Simulation).filter(Simulation.user_id == user_id).order_by(
        Simulation.created_at.desc()
    ).offset(skip).limit(limit).all()

def get_simulation(db: Session, simulation_id: UUID, user_id: UUID) -> Optional[Simulation]:
    """Get a specific simulation by ID"""
    return db.query(Simulation).filter(
        Simulation.id == simulation_id,
        Simulation.user_id == user_id
    ).first()

def update_simulation(db: Session, simulation: Simulation, simulation_in: SimulationUpdate) -> Simulation:
    """Update simulation details"""
    update_data = simulation_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(simulation, field, value)
    
    db.add(simulation)
    db.commit()
    db.refresh(simulation)
    return simulation

def start_simulation(db: Session, simulation_id: UUID, user_id: UUID) -> Optional[Simulation]:
    """Start a simulation"""
    simulation = get_simulation(db, simulation_id, user_id)
    
    if not simulation or simulation.status != "pending":
        return None
    
    # Update simulation status
    simulation.status = "starting"
    simulation.start_time = datetime.now()
    db.add(simulation)
    db.commit()
    db.refresh(simulation)
    
    # Start the background task
    start_simulation_background_task(
        simulation_id=simulation.id,
        target_honeypot_id=simulation.target_honeypot_id,
        attack_type=simulation.attack_type,
        node_count=simulation.node_count,
        duration_minutes=simulation.duration_minutes,
        intensity=simulation.intensity
    )
    
    return simulation