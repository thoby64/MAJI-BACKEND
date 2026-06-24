"""
Constants and Enums
Application-wide constants and enumeration definitions
"""

from enum import Enum


class EntityStatus(str, Enum):
    """Entity status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ReportStatus(str, Enum):
    """Report status enumeration"""
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class ReportPriority(str, Enum):
    """Report priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LeakageType(str, Enum):
    """Reported leakage type enumeration"""
    GROUND_LEAKAGE = "ground_leakage"
    PIPE_BURST = "pipe_burst"
    METER_LEAKAGE = "meter_leakage"
    VALVE_LEAKAGE = "valve_leakage"
    OVERFLOW = "overflow"
    UNKNOWN = "unknown"


class NotificationType(str, Enum):
    """Notification type enumeration"""
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    ERROR = "error"


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    UTILITY_MANAGER = "utility_manager"
    DMA_MANAGER = "dma_manager"
    ENGINEER = "engineer"
