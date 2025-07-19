# Import Base from session to avoid circular imports
from app.db.session import Base

# Import all models here so that Alembic can discover them
from app.models import *  # noqa