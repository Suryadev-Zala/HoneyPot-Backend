import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Simulation(Base):
    __tablename__ = "simulations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    attack_type = Column(String, nullable=False)  # brute-force, web-attack, etc.
    target_honeypot_id = Column(UUID(as_uuid=True), ForeignKey("honeypots.id"))
    node_count = Column(Integer, default=5)
    duration_minutes = Column(Integer, default=5)
    intensity = Column(Integer, default=5)  # 1-10
    status = Column(String, default="pending")  # pending, running, completed, failed
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    results = Column(JSON, default={})
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="simulations")
    target_honeypot = relationship("Honeypot", back_populates="simulations")
    attacks = relationship("Attack", back_populates="simulation")