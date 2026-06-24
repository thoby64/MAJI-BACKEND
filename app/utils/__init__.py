"""
Utils Package
Utility functions and helpers
"""

from app.utils.tracking_id import generate_tracking_id
from app.utils.response_models import (
    APIResponse,
    APIError,
    PaginatedResponse,
    HealthResponse,
)
from app.utils.exceptions import (
    MajiscopeException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    InternalServerError,
)
from app.utils.api_utils import (
    apply_pagination,
    apply_sorting,
    apply_filters,
    get_or_404,
    paginate,
    obj_to_dict,
    check_duplicate,
)

__all__ = [
    "generate_tracking_id",
    "APIResponse",
    "APIError",
    "PaginatedResponse",
    "HealthResponse",
    "MajiscopeException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "InternalServerError",
    "apply_pagination",
    "apply_sorting",
    "apply_filters",
    "get_or_404",
    "paginate",
    "obj_to_dict",
    "check_duplicate",
]
