"""
API Package
API route handlers organized by resource
"""

from app.api.auth import auth_router
from app.api.users import users_router
from app.api.utilities import utilities_router
from app.api.dmas import dmas_router
from app.api.teams import teams_router
from app.api.engineers import engineers_router
from app.api.reports import reports_router
from app.api.utility_managers import utility_managers_router
from app.api.dma_managers import dma_managers_router
from app.api.notifications import notifications_router
from app.api.push_tokens import push_tokens_router
from app.api.logs import logs_router
from app.api.health import health_router
from app.api.uploads import uploads_router

__all__ = [
    "auth_router",
    "users_router",
    "utilities_router",
    "dmas_router",
    "teams_router",
    "engineers_router",
    "reports_router",
    "utility_managers_router",
    "dma_managers_router",
    "notifications_router",
    "push_tokens_router",
    "logs_router",
    "health_router",
    "uploads_router",
]
