# Routes Package Initialization
# This module initializes the routes package and makes all route modules available for import

# Import all route modules
from . import (
    health,
    excel,
    bse,
    sebi,
    rbi,
    analytics,
    admin,
    directors,
    directors_disclosure,
    director_analysis,
    minutes,
    ai_assistant,
    chat,
    visit_tracking,
    insider_trading,
    director_family_info
)

# Export all routers
__all__ = [
    "health",
    "excel",
    "bse",
    "sebi",
    "rbi",
    "analytics",
    "admin",
    "directors",
    "directors_disclosure",
    "director_analysis",
    "minutes",
    "ai_assistant",
    "chat",
    "visit_tracking",
    "insider_trading",
    "director_family_info"
]
