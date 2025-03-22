import docker
import uuid
import logging
from typing import Dict, Optional, List, Any
from app.core.config import settings
from app.models.honeypot import Honeypot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Docker client
try:
    docker_client = docker.from_env()
    # Create network if it doesn't exist
    try:
        docker_client.networks.get(settings.DOCKER_NETWORK)
    except docker.errors.NotFound:
        docker_client.networks.create(settings.DOCKER_NETWORK)
        logger.info(f"Created Docker network: {settings.DOCKER_NETWORK}")
except Exception as e:
    logger.error(f"Failed to initialize Docker client: {str(e)}")
    docker_client = None

def get_honeypot_image(honeypot_type: str) -> str:
    """Get Docker image name for honeypot type"""
    return settings.HONEYPOT_IMAGES.get(honeypot_type, "cowrie/cowrie:latest")

def prepare_environment(honeypot: Honeypot) -> Dict[str, str]:
    """Prepare environment variables for the honeypot container"""
    env_vars = {
        "HONEYPOT_ID": str(honeypot.id),
        "HONEYPOT_NAME": honeypot.name,
        "HONEYPOT_TYPE": honeypot.type,
    }
    
    # Add emulated system if specified
    if honeypot.emulated_system:
        env_vars["EMULATED_SYSTEM"] = honeypot.emulated_system
    
    # Add custom configuration
    if honeypot.configuration:
        for key, value in honeypot.configuration.items():
            # Convert to string and prefix with CONFIG_
            if isinstance(value, (dict, list)):
                continue  # Skip complex types
            env_vars[f"CONFIG_{key.upper()}"] = str(value)
    
    return env_vars

def prepare_port_mapping(honeypot: Honeypot) -> Dict[str, int]:
    """Prepare port mappings for the honeypot container"""
    port_mappings = {}
    
    # Split ports by comma and create mappings
    ports = honeypot.port.split(",")
    for port in ports:
        port = port.strip()
        if port.isdigit():
            # Map container port to same host port
            port_mappings[f"{port}/tcp"] = int(port)
    
    return port_mappings

def deploy_honeypot_instance(honeypot: Honeypot) -> bool:
    """Deploy a honeypot container"""
    if not docker_client:
        logger.error("Docker client not available")
        return False
    
    try:
        # Get image for honeypot type
        image = get_honeypot_image(honeypot.type)
        
        # Prepare container configuration
        env_vars = prepare_environment(honeypot)
        port_mappings = prepare_port_mapping(honeypot)
        container_name = f"honeypot-{honeypot.id}"
        
        # Create volume for logs
        volume_name = f"honeypot-logs-{honeypot.id}"
        docker_client.volumes.create(name=volume_name)
        
        # Deploy container
        container = docker_client.containers.run(
            image=image,
            detach=True,
            name=container_name,
            environment=env_vars,
            ports=port_mappings,
            network=settings.DOCKER_NETWORK,
            volumes={
                volume_name: {'bind': '/var/log/honeypot', 'mode': 'rw'}
            },
            restart_policy={"Name": "unless-stopped"}
        )
        
        logger.info(f"Deployed honeypot container: {container.id} for honeypot {honeypot.id}")
        return True
    
    except Exception as e:
        logger.error(f"Error deploying honeypot container: {str(e)}")
        return False

def update_honeypot_instance(honeypot: Honeypot) -> bool:
    """Update a honeypot container"""
    if not docker_client:
        return False
    
    try:
        # First stop and remove existing container
        remove_honeypot_instance(honeypot)
        
        # Then create a new container with updated configuration
        return deploy_honeypot_instance(honeypot)
    
    except Exception as e:
        logger.error(f"Error updating honeypot container: {str(e)}")
        return False

def remove_honeypot_instance(honeypot: Honeypot) -> bool:
    """Remove a honeypot container"""
    if not docker_client:
        return False
    
    try:
        container_name = f"honeypot-{honeypot.id}"
        
        # Find container by name
        try:
            container = docker_client.containers.get(container_name)
            
            # Stop and remove container
            container.stop()
            container.remove()
            
            # Remove volume
            volume_name = f"honeypot-logs-{honeypot.id}"
            try:
                volume = docker_client.volumes.get(volume_name)
                volume.remove()
            except:
                pass
            
            logger.info(f"Removed honeypot container for honeypot {honeypot.id}")
            return True
        
        except docker.errors.NotFound:
            # Container not found, consider it removed
            return True
    
    except Exception as e:
        logger.error(f"Error removing honeypot container: {str(e)}")
        return False

def get_honeypot_status(honeypot: Honeypot) -> str:
    """Get current status of honeypot container"""
    if not docker_client:
        return "unknown"
    
    try:
        container_name = f"honeypot-{honeypot.id}"
        
        try:
            container = docker_client.containers.get(container_name)
            return container.status
        except docker.errors.NotFound:
            return "not_deployed"
    
    except Exception as e:
        logger.error(f"Error checking honeypot status: {str(e)}")
        return "error"