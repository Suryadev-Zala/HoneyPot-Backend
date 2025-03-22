import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy import Boolean

class Attack(Base):
    __tablename__ = "attacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    honeypot_id = Column(UUID(as_uuid=True), ForeignKey("honeypots.id"))
    source_ip = Column(String)
    attack_type = Column(String)  # brute-force, sql-injection, etc.
    severity = Column(String)  # low, medium, high
    details = Column(JSON)
    is_simulated = Column(Boolean, default=False)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    honeypot = relationship("Honeypot", back_populates="attacks")
    simulation = relationship("Simulation", back_populates="attacks")