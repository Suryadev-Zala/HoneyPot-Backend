from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import simulation as simulation_schemas
from app.services import simulation_service
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.simulation import Simulation

router = APIRouter()

@router.post("/", response_model=simulation_schemas.Simulation, status_code=status.HTTP_201_CREATED)
def create_simulation(
    simulation_in: simulation_schemas.SimulationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new simulation"""
    return simulation_service.create_simulation(db=db, simulation_in=simulation_in, user_id=current_user.id)

@router.get("/", response_model=List[simulation_schemas.Simulation])
def get_simulations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all simulations for the current user"""
    return simulation_service.get_simulations(db=db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{simulation_id}", response_model=simulation_schemas.Simulation)
def get_simulation(
    simulation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific simulation"""
    simulation = simulation_service.get_simulation(db=db, simulation_id=simulation_id, user_id=current_user.id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulation

@router.put("/{simulation_id}/status")
def update_simulation_status(
    simulation_id: UUID,
    update: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update simulation status (internal API)"""
    # This endpoint is used by the background task
    # We don't check user_id for this endpoint as it's called internally
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulation_update = simulation_schemas.SimulationUpdate(
        status=update.get("status"),
        results=update.get("results")
    )
    
    return simulation_service.update_simulation(db=db, simulation=simulation, simulation_in=simulation_update)

@router.post("/{simulation_id}/start", response_model=simulation_schemas.Simulation)
def start_simulation(
    simulation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a simulation"""
    simulation = simulation_service.start_simulation(db=db, simulation_id=simulation_id, user_id=current_user.id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found or invalid status")
    
    return simulation