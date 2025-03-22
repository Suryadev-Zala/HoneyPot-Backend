import random
import string
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import httpx
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.simulation import Simulation
from app.models.attack import Attack
from app.core.config import settings

logger = logging.getLogger(__name__)

# Attack patterns for different types
ATTACK_PATTERNS = {
    "SSH-BRUTEFORCE": {
        "usernames": ["root", "admin", "user", "test", "oracle", "postgres", "ubuntu"],
        "password_patterns": ["password", "123456", "admin", "root", "qwerty"],
    },
    "WEB-SQL-INJECTION": {
        "patterns": [
            "' OR 1=1--",
            "admin' --",
            "' UNION SELECT * FROM users--",
            "1'; DROP TABLE users--",
        ]
    },
    "FTP-BRUTEFORCE": {
        "usernames": ["anonymous", "admin", "ftp", "user"],
        "password_patterns": ["", "admin", "password", "ftp"]
    }
}

async def generate_attack(attack_type: str, intensity: int) -> Dict[str, Any]:
    """Generate a simulated attack based on type and intensity"""
    ip_octets = [str(random.randint(1, 255)) for _ in range(4)]
    source_ip = ".".join(ip_octets)
    
    if attack_type == "SSH-BRUTEFORCE":
        username = random.choice(ATTACK_PATTERNS["SSH-BRUTEFORCE"]["usernames"])
        password = random.choice(ATTACK_PATTERNS["SSH-BRUTEFORCE"]["password_patterns"])
        
        # Add some complexity to password based on intensity
        if intensity > 5:
            password += ''.join(random.choices(string.ascii_letters + string.digits, k=intensity))
        
        return {
            "source_ip": source_ip,
            "type": attack_type,
            "severity": "medium" if intensity > 7 else "low",
            "details": {
                "username": username,
                "password": password,
                "attempt_count": random.randint(1, intensity * 2)
            }
        }
    
    elif attack_type == "WEB-SQL-INJECTION":
        pattern = random.choice(ATTACK_PATTERNS["WEB-SQL-INJECTION"]["patterns"])
        
        return {
            "source_ip": source_ip,
            "type": attack_type,
            "severity": "high",
            "details": {
                "pattern": pattern,
                "url": f"/admin?id={pattern}",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
            }
        }
    
    elif attack_type == "FTP-BRUTEFORCE":
        username = random.choice(ATTACK_PATTERNS["FTP-BRUTEFORCE"]["usernames"])
        password = random.choice(ATTACK_PATTERNS["FTP-BRUTEFORCE"]["password_patterns"])
        
        return {
            "source_ip": source_ip,
            "type": attack_type,
            "severity": "medium",
            "details": {
                "username": username,
                "password": password,
                "commands": ["LIST", "RETR", "STOR"]
            }
        }
    
    else:
        return {
            "source_ip": source_ip,
            "type": "GENERIC",
            "severity": "low",
            "details": {
                "info": "Unknown attack type simulation"
            }
        }

async def run_simulation_task(
    db_url: str,
    simulation_id: UUID,
    target_honeypot_id: UUID,
    attack_type: str,
    node_count: int,
    duration_minutes: int,
    intensity: int
) -> None:
    """Run the attack simulation as a background task"""
    try:
        # Setup database connection
        async with httpx.AsyncClient() as client:
            # Update simulation status to running
            await client.put(
                f"{db_url}/simulations/{simulation_id}/status",
                json={"status": "running", "start_time": datetime.now().isoformat()}
            )
            
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            # Calculate attack frequency
            total_attacks = intensity * 10 * duration_minutes
            delay_between_attacks = (duration_minutes * 60) / total_attacks
            
            attack_count = 0
            while datetime.now() < end_time:
                # Generate attacks from different nodes
                for _ in range(node_count):
                    if random.random() < 0.7:  # 70% chance of attack from each node
                        attack = await generate_attack(attack_type, intensity)
                        
                        # Record the attack
                        await client.post(
                            f"{db_url}/attacks",
                            json={
                                "honeypot_id": str(target_honeypot_id),
                                "simulation_id": str(simulation_id),
                                "source_ip": attack["source_ip"],
                                "attack_type": attack["type"],
                                "severity": attack["severity"],
                                "details": attack["details"],
                                "is_simulated": True
                            }
                        )
                        attack_count += 1
                
                # Wait before next attack
                await asyncio.sleep(delay_between_attacks)
            
            # Update simulation to completed
            await client.put(
                f"{db_url}/simulations/{simulation_id}/status",
                json={
                    "status": "completed",
                    "end_time": datetime.now().isoformat(),
                    "results": {
                        "total_attacks": attack_count,
                        "attack_type": attack_type,
                        "duration_minutes": duration_minutes,
                        "intensity": intensity,
                        "node_count": node_count
                    }
                }
            )
    
    except Exception as e:
        logger.error(f"Error in simulation {simulation_id}: {str(e)}")
        
        # Update simulation to failed status
        try:
            async with httpx.AsyncClient() as client:
                await client.put(
                    f"{db_url}/simulations/{simulation_id}/status",
                    json={
                        "status": "failed",
                        "results": {"error": str(e)}
                    }
                )
        except Exception:
            pass

def start_simulation_background_task(
    simulation_id: UUID,
    target_honeypot_id: UUID,
    attack_type: str,
    node_count: int,
    duration_minutes: int,
    intensity: int
) -> None:
    """Start background task for simulation"""
    # We need to use an API call because the task runs in a separate process
    db_url = f"http://localhost:8000{settings.API_V1_STR}"
    
    # Create and start the task
    asyncio.create_task(run_simulation_task(
        db_url=db_url,
        simulation_id=simulation_id,
        target_honeypot_id=target_honeypot_id,
        attack_type=attack_type,
        node_count=node_count,
        duration_minutes=duration_minutes,
        intensity=intensity
    ))