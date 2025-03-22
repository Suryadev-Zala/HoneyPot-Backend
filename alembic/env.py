import os
import sys
from dotenv import load_dotenv
from alembic import context  # Import context for Alembic
from alembic.config import Config  # Import Config for Alembic

# Add app module to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import your models and config
from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.honeypot import Honeypot
from app.models.attack import Attack
from app.models.simulation import Simulation

# Initialize Alembic config
config = context.config  # Use Alembic's context to get the config

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# In the run_migrations_online() function:
target_metadata = Base.metadata