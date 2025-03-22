from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.models.attack import Attack
from app.models.honeypot import Honeypot
from app.api.dependencies import get_current_user
from app.models.user import User
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics summary for dashboard"""
    # Get user honeypots
    honeypots = db.query(Honeypot).filter(Honeypot.user_id == current_user.id).all()
    honeypot_ids = [h.id for h in honeypots]
    
    # Skip if no honeypots
    if not honeypot_ids:
        return {
            "totalAttacks": 0,
            "activeHoneypots": 0,
            "topAttackTypes": [],
            "recentAttacks": []
        }
    
    # Get total attacks
    total_attacks = db.query(func.count(Attack.id)).filter(Attack.honeypot_id.in_(honeypot_ids)).scalar() or 0
    
    # Get active honeypots
    active_honeypots = len([h for h in honeypots if h.status == "active"])
    
    # Get top attack types
    top_attack_types = db.query(
        Attack.attack_type,
        func.count(Attack.id).label("count")
    ).filter(
        Attack.honeypot_id.in_(honeypot_ids)
    ).group_by(
        Attack.attack_type
    ).order_by(
        desc("count")
    ).limit(5).all()
    
    # Get recent attacks
    recent_attacks = db.query(Attack).filter(
        Attack.honeypot_id.in_(honeypot_ids)
    ).order_by(
        Attack.timestamp.desc()
    ).limit(10).all()
    
    return {
        "totalAttacks": total_attacks,
        "activeHoneypots": active_honeypots,
        "topAttackTypes": [{"type": t.attack_type, "count": t.count} for t in top_attack_types],
        "recentAttacks": [
            {
                "id": str(a.id),
                "timestamp": a.timestamp,
                "source_ip": a.source_ip,
                "attack_type": a.attack_type,
                "severity": a.severity,
                "honeypot_id": str(a.honeypot_id),
                "is_simulated": a.is_simulated
            } for a in recent_attacks
        ]
    }

@router.get("/attack-distribution")
def get_attack_distribution(
    time_period: str = "7d",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get distribution of attacks by type"""
    # Get user honeypots
    honeypots = db.query(Honeypot).filter(Honeypot.user_id == current_user.id).all()
    honeypot_ids = [h.id for h in honeypots]
    
    if not honeypot_ids:
        return {"data": []}
    
    # Calculate time filter
    now = datetime.now()
    if time_period == "24h":
        time_filter = now - timedelta(days=1)
    elif time_period == "7d":
        time_filter = now - timedelta(days=7)
    elif time_period == "30d":
        time_filter = now - timedelta(days=30)
    else:
        time_filter = now - timedelta(days=7)  # Default to 7 days
    
    # Query attack distribution
    attack_distribution = db.query(
        Attack.attack_type,
        func.count(Attack.id).label("count")
    ).filter(
        Attack.honeypot_id.in_(honeypot_ids),
        Attack.timestamp >= time_filter
    ).group_by(
        Attack.attack_type
    ).order_by(
        desc("count")
    ).all()
    
    return {
        "data": [
            {
                "attack_type": a.attack_type, 
                "count": a.count
            } for a in attack_distribution
        ]
    }

@router.get("/attack-sources")
def get_attack_sources(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top attack sources by IP"""
    # Get user honeypots
    honeypots = db.query(Honeypot).filter(Honeypot.user_id == current_user.id).all()
    honeypot_ids = [h.id for h in honeypots]
    
    if not honeypot_ids:
        return {"data": []}
    
    # Query attack sources
    attack_sources = db.query(
        Attack.source_ip,
        func.count(Attack.id).label("count")
    ).filter(
        Attack.honeypot_id.in_(honeypot_ids)
    ).group_by(
        Attack.source_ip
    ).order_by(
        desc("count")
    ).limit(limit).all()
    
    return {
        "data": [
            {
                "source_ip": a.source_ip, 
                "count": a.count
            } for a in attack_sources
        ]
    }