"""
Pydantic schemas for Business-related models
Request and response models for API validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.constants.enums import LeakageType, ReportStatus, ReportPriority, NotificationType


# ============================================================================
# Report Schemas
# ============================================================================

class ReportBase(BaseModel):
    """Base schema for Report"""
    tracking_id: str = Field(..., min_length=1, max_length=50)
    dma_id: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    priority: ReportPriority = ReportPriority.MEDIUM
    leakage_type: LeakageType = LeakageType.UNKNOWN
    photos: Optional[List[str]] = []


class ReportCreate(ReportBase):
    """Schema for creating a report"""
    assigned_engineer_id: Optional[str] = None


class AnonymousReportCreate(BaseModel):
    """Schema for creating anonymous reports from mobile app"""
    description: str = Field(..., max_length=2000)
    latitude: float
    longitude: float
    address: Optional[str] = Field(None, max_length=500)
    priority: str = "Medium"  # Accept string priority from mobile app
    leakage_type: LeakageType = LeakageType.UNKNOWN
    images: Optional[List[str]] = []
    reported_by: Optional[str] = "Anonymous"


class ReportUpdate(BaseModel):
    """Schema for updating report"""
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[ReportPriority] = None
    leakage_type: Optional[LeakageType] = None
    assigned_engineer_id: Optional[str] = None
    status: Optional[ReportStatus] = None
    photos: Optional[List[str]] = None
    sla_deadline: Optional[datetime] = None


class ReportResponse(ReportBase):
    """Schema for report response"""
    id: str
    status: ReportStatus
    assigned_engineer_id: Optional[str]
    sla_deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for list of reports"""
    total: int
    items: List[ReportResponse]


class ReportStatusUpdateRequest(BaseModel):
    """Schema for updating report status"""
    status: ReportStatus = Field(..., description="New report status")
    notes: Optional[str] = Field(None, max_length=500, description="Status update notes")


class ReportReviewDecisionRequest(BaseModel):
    """Schema for DMA review decisions on a completed report."""
    notes: Optional[str] = Field(None, max_length=500, description="Optional DMA approval or rework comment")


# ============================================================================
# Activity Log Schemas
# ============================================================================

class ActivityLogBase(BaseModel):
    """Base schema for ActivityLog"""
    user_id: Optional[str] = None
    utility_mgr_id: Optional[str] = None
    dma_mgr_id: Optional[str] = None
    engineer_id: Optional[str] = None
    user_name: str = Field(..., min_length=1, max_length=255)
    user_role: str = Field(..., min_length=1, max_length=50)
    action: str = Field(..., min_length=1, max_length=255)
    entity: str = Field(..., min_length=1, max_length=100)
    entity_id: str
    details: Optional[str] = Field(None, max_length=2000)
    utility_id: Optional[str] = None
    dma_id: Optional[str] = None


class ActivityLogCreate(ActivityLogBase):
    """Schema for creating an activity log"""
    pass


class ActivityLogResponse(ActivityLogBase):
    """Schema for activity log response"""
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ActivityLogListResponse(BaseModel):
    """Schema for list of activity logs"""
    total: int
    items: List[ActivityLogResponse]


class ActivityLogFilterRequest(BaseModel):
    """Schema for filtering activity logs"""
    user_id: Optional[str] = None
    action: Optional[str] = None
    entity: Optional[str] = None
    entity_id: Optional[str] = None
    utility_id: Optional[str] = None
    dma_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# ============================================================================
# Notification Schemas
# ============================================================================

class NotificationBase(BaseModel):
    """Base schema for Notification"""
    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=2000)
    is_read: bool = False
    data: Optional[Dict[str, Any]] = None
    link: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    user_id: Optional[str] = None
    utility_manager_id: Optional[str] = None
    dma_manager_id: Optional[str] = None
    engineer_id: Optional[str] = None

    class Config:
        # Allow at least one recipient ID to be set
        pass


class NotificationUpdate(BaseModel):
    """Schema for updating notification"""
    is_read: Optional[bool] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1, max_length=2000)
    data: Optional[Dict[str, Any]] = None
    link: Optional[str] = None


class NotificationResponse(NotificationBase):
    """Schema for notification response"""
    id: str
    user_id: Optional[str]
    utility_manager_id: Optional[str]
    dma_manager_id: Optional[str]
    engineer_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for list of notifications"""
    total: int
    items: List[NotificationResponse]


class NotificationBulkCreate(BaseModel):
    """Schema for creating notifications for multiple recipients"""
    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=2000)
    user_ids: Optional[List[str]] = []
    utility_manager_ids: Optional[List[str]] = []
    dma_manager_ids: Optional[List[str]] = []
    engineer_ids: Optional[List[str]] = []
    data: Optional[Dict[str, Any]] = None
    link: Optional[str] = None


class PushTokenRegisterRequest(BaseModel):
    expo_push_token: str = Field(..., min_length=1, max_length=255)
    platform: Optional[str] = Field(None, max_length=32)
    device_name: Optional[str] = Field(None, max_length=255)
    device_id: Optional[str] = Field(None, max_length=255)
    app_role: Optional[str] = Field(None, max_length=50)


class PushTokenResponse(BaseModel):
    id: str
    expo_push_token: str
    platform: Optional[str] = None
    device_name: Optional[str] = None
    device_id: Optional[str] = None
    app_role: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime
    last_registered_at: datetime

    class Config:
        from_attributes = True
