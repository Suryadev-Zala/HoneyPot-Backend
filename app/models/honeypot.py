import uuid
from sqlalchemy import Column, String, Boolean, Integer, JSON, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Honeypot(Base):
    __tablename__ = "honeypots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # SSH, Web, FTP, etc.
    ip_address = Column(String, nullable=False)
    port = Column(String, nullable=False)  # Can be multiple ports as CSV
    status = Column(String, default="inactive")  # active, inactive, error
    emulated_system = Column(String)
    configuration = Column(JSON, default={})
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    container_id = Column(String)
    description = Column(Text)
    attack_count = Column(Integer, default=0)
    vulnerabilities = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="honeypots")
    attacks = relationship("Attack", back_populates="honeypot", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="target_honeypot")