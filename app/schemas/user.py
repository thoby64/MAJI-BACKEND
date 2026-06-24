"""
Pydantic schemas for User-related models
Request and response models for API validation
"""

from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.constants.enums import EntityStatus


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base schema for User"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    avatar: Optional[str] = Field(None, max_length=255)
    status: EntityStatus = EntityStatus.ACTIVE


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=255)


class UserUpdate(BaseModel):
    """Schema for updating user details"""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    avatar: Optional[str] = Field(None, max_length=255)
    status: Optional[EntityStatus] = None
    password: Optional[str] = Field(None, min_length=8, max_length=255)


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    created_at: datetime
    updated_at: datetime
    user_type: str = "user"  # Type of user: user, utility_manager, dma_manager, engineer
    role: Optional[str] = None  # For engineers: "engineer" or "team_leader"
    # Manager-specific fields
    utility_id: Optional[str] = None
    utility_name: Optional[str] = None
    dma_id: Optional[str] = None
    dma_name: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    onboarding_status: str = "completed"
    invite_expires_at: Optional[datetime] = None
    setup_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for list of users"""
    total: int
    items: List[UserResponse]


class UserInvitationCreate(BaseModel):
    """Schema for inviting a public-report user."""
    email: EmailStr
    status: EntityStatus = EntityStatus.ACTIVE


# ============================================================================
# Utility Schemas
# ============================================================================

UTILITY_SERVICE_AREA_CATEGORIES = {
    "region",
    "district",
    "city",
    "town",
    "ward",
    "village",
    "custom_area",
    "infrastructure_corridor",
}


class UtilityServiceAreaBase(BaseModel):
    """Official named service area for a utility."""

    category: str = Field(..., description="Service area category")
    name: str = Field(..., min_length=1, max_length=255)
    region_name: Optional[str] = Field(None, max_length=100)
    admin_area_id: Optional[str] = Field(None, max_length=100)

    @classmethod
    def _normalize_category(cls, value: str) -> str:
        normalized = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in UTILITY_SERVICE_AREA_CATEGORIES:
            raise ValueError("Unsupported utility service area category")
        return normalized

    def model_post_init(self, __context: Any) -> None:
        self.category = self._normalize_category(self.category)
        self.name = self.name.strip()
        if self.region_name is not None:
            self.region_name = self.region_name.strip() or None
        if self.admin_area_id is not None:
            self.admin_area_id = self.admin_area_id.strip() or None


class UtilityServiceAreaCreate(UtilityServiceAreaBase):
    """Schema for utility service area creation."""


class UtilityServiceAreaResponse(UtilityServiceAreaBase):
    """Schema for utility service area response."""

    id: str
    utility_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UtilityBase(BaseModel):
    """Base schema for Utility"""
    name: str = Field(..., min_length=1, max_length=255)
    region_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None
    contact_address: Optional[str] = Field(None, max_length=255)
    center_latitude: Optional[float] = Field(None, ge=-90, le=90)
    center_longitude: Optional[float] = Field(None, ge=-180, le=180)
    boundary_geojson: Optional[dict[str, Any]] = None
    boundary_source_type: Optional[str] = Field("none", max_length=32)
    boundary_status: Optional[str] = Field("none", max_length=32)
    service_areas: List[UtilityServiceAreaCreate] = Field(default_factory=list)
    status: EntityStatus = EntityStatus.ACTIVE


class UtilityCreate(UtilityBase):
    """Schema for creating a utility"""
    pass


class UtilityUpdate(BaseModel):
    """Schema for updating utility"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    region_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None
    contact_address: Optional[str] = Field(None, max_length=255)
    center_latitude: Optional[float] = Field(None, ge=-90, le=90)
    center_longitude: Optional[float] = Field(None, ge=-180, le=180)
    boundary_geojson: Optional[dict[str, Any]] = None
    boundary_source_type: Optional[str] = Field(None, max_length=32)
    boundary_status: Optional[str] = Field(None, max_length=32)
    service_areas: Optional[List[UtilityServiceAreaCreate]] = None
    status: Optional[EntityStatus] = None


class UtilityInfrastructureAssetResponse(BaseModel):
    """Stored infrastructure asset metadata for a utility."""

    asset_type: str
    label: str
    file_name: str
    file_size: int
    mime_type: str
    feature_count: int = 0
    download_url: str
    preview_url: str
    uploaded_at: datetime


class UtilityResponse(UtilityBase):
    """Schema for utility response"""
    id: str
    service_areas: List[UtilityServiceAreaResponse] = Field(default_factory=list)
    infrastructure_layers: List[UtilityInfrastructureAssetResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PipeNetworkIngestSummary(BaseModel):
    """Upload-time ingestion and cleaning summary for utility infrastructure files."""

    total_features_read: int = 0
    previewable_features: int = 0
    skipped_features: int = 0
    skipped_missing_geometry: int = 0
    skipped_invalid_geometry: int = 0
    skipped_unsupported_geometry: int = 0
    missing_material: int = 0
    missing_condition: int = 0
    missing_diameter: int = 0
    missing_location: int = 0
    source_layers: List[str] = []
    has_warnings: bool = False


class UtilityInfrastructureUploadResponse(BaseModel):
    """Response payload for infrastructure asset uploads."""

    utility: UtilityResponse
    asset: UtilityInfrastructureAssetResponse
    ingest_summary: PipeNetworkIngestSummary


class UtilityListResponse(BaseModel):
    """Schema for list of utilities"""
    total: int
    items: List[UtilityResponse]


class UtilityPublicContactResponse(BaseModel):
    """Resolved public utility and DMA contacts for a given location."""

    utility_id: str
    utility_name: str
    region_name: Optional[str] = None
    dma_id: Optional[str] = None
    dma_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_address: Optional[str] = None


# ============================================================================
# Utility Manager Schemas
# ============================================================================

class UtilityManagerBase(BaseModel):
    """Base schema for UtilityManager"""
    name: str
    email: str
    phone: Optional[str] = None
    status: str = "active"
    utility_id: Optional[str] = None


class UtilityManagerCreate(UtilityManagerBase):
    """Schema for creating a utility manager"""
    password: str


class UtilityManagerUpdate(BaseModel):
    """Schema for updating a utility manager."""
    name: str
    email: str
    phone: Optional[str] = None
    status: str = "active"
    utility_id: Optional[str] = None
    password: Optional[str] = None


class UtilityManagerResponse(UtilityManagerBase):
    """Schema for utility manager response"""
    id: str
    avatar: Optional[str] = None
    onboarding_status: str = "completed"
    invite_expires_at: Optional[datetime] = None
    setup_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UtilityManagerListResponse(BaseModel):
    """Schema for list of utility managers"""
    total: int
    items: List[UtilityManagerResponse]


class UtilityManagerInvitationCreate(BaseModel):
    """Schema for inviting a utility manager."""
    email: EmailStr
    utility_id: str
    status: EntityStatus = EntityStatus.ACTIVE


# ============================================================================
# DMA Schemas (District Metering Area)
# ============================================================================

class DMABase(BaseModel):
    """Base schema for DMA"""
    utility_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    center_latitude: Optional[float] = Field(None, ge=-90, le=90)
    center_longitude: Optional[float] = Field(None, ge=-180, le=180)
    boundary_geojson: Optional[dict[str, Any]] = None
    status: EntityStatus = EntityStatus.ACTIVE


class DMACreate(DMABase):
    """Schema for creating a DMA"""
    pass


class DMAUpdate(BaseModel):
    """Schema for updating DMA"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    center_latitude: Optional[float] = Field(None, ge=-90, le=90)
    center_longitude: Optional[float] = Field(None, ge=-180, le=180)
    boundary_geojson: Optional[dict[str, Any]] = None
    status: Optional[EntityStatus] = None


class DMAResponse(DMABase):
    """Schema for DMA response"""
    id: str
    utility_name: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    teams_count: int = 0
    reports_count: int = 0
    engineers_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DMAListResponse(BaseModel):
    """Schema for list of DMAs"""
    total: int
    items: List[DMAResponse]


# ============================================================================
# DMA Manager Schemas
# ============================================================================

class DMAManagerBase(BaseModel):
    """Base schema for DMAManager"""
    name: str
    email: str
    phone: Optional[str] = None
    status: str = "active"
    utility_id: str
    dma_id: Optional[str] = None


class DMAManagerCreate(DMAManagerBase):
    """Schema for creating a DMA manager"""
    password: str


class DMAManagerUpdate(BaseModel):
    """Schema for updating a DMA manager"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    utility_id: Optional[str] = None
    dma_id: Optional[str] = None
    password: Optional[str] = None  # Optional for updates


class DMAManagerResponse(DMAManagerBase):
    """Schema for DMA manager response"""
    id: str
    avatar: Optional[str] = None
    utility_name: Optional[str] = None
    dma_name: Optional[str] = None
    onboarding_status: str = "completed"
    invite_expires_at: Optional[datetime] = None
    setup_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DMAManagerListResponse(BaseModel):
    """Schema for list of DMA managers"""
    total: int
    items: List[DMAManagerResponse]


class DMAManagerInvitationCreate(BaseModel):
    """Schema for inviting a DMA manager."""
    email: EmailStr
    utility_id: str
    dma_id: Optional[str] = None
    status: EntityStatus = EntityStatus.ACTIVE


# ============================================================================
# Team Schemas
# ============================================================================

class TeamBase(BaseModel):
    """Base schema for Team"""
    dma_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: EntityStatus = EntityStatus.ACTIVE


class TeamCreate(TeamBase):
    """Schema for creating a team"""
    pass


class TeamUpdate(BaseModel):
    """Schema for updating team"""
    dma_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[EntityStatus] = None


class TeamResponse(TeamBase):
    """Schema for team response"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamListResponse(BaseModel):
    """Schema for list of teams"""
    total: int
    items: List[TeamResponse]


# ============================================================================
# Engineer Schemas
# ============================================================================

class EngineerBase(BaseModel):
    """Base schema for Engineer"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    team_id: str
    dma_id: Optional[str] = None
    role: str = Field(default="engineer", pattern="^(engineer|team_leader)$")
    status: EntityStatus = EntityStatus.ACTIVE
    specialization: Optional[str] = Field(None, max_length=255)


class EngineerCreate(BaseModel):
    """Schema for creating an engineer"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    team_id: str
    dma_id: Optional[str] = None
    role: str = Field(default="engineer", pattern="^(engineer|team_leader)$")
    status: EntityStatus = EntityStatus.ACTIVE


class EngineerUpdate(BaseModel):
    """Schema for updating engineer"""
    id: str  # Required for update operations
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    dma_id: Optional[str] = None
    team_id: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(engineer|team_leader)$")
    status: Optional[EntityStatus] = None
    password: Optional[str] = Field(None, min_length=8, max_length=255)


class EngineerResponse(BaseModel):
    """Schema for engineer response"""
    id: str
    name: str
    email: str
    phone: Optional[str]
    dma_id: str
    team_id: Optional[str]
    team_name: Optional[str] = None
    status: str
    role: str
    onboarding_status: str = "completed"
    invite_expires_at: Optional[datetime] = None
    setup_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EngineerListResponse(BaseModel):
    """Schema for list of engineers"""
    total: int
    items: List[EngineerResponse]


class EngineerInvitationCreate(BaseModel):
    """Schema for inviting an engineer or team leader."""
    email: EmailStr
    team_id: str
    role: str = Field(default="engineer", pattern="^(engineer|team_leader)$")
    status: EntityStatus = EntityStatus.ACTIVE


class EngineerInvitationBulkCreate(BaseModel):
    """Schema for bulk engineer invitations."""
    invitations: List[EngineerInvitationCreate]


class EngineerInvitationValidateResponse(BaseModel):
    """Schema for validating an invitation token."""
    valid: bool
    message: str
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    dma_id: Optional[str] = None
    dma_name: Optional[str] = None
    expires_at: Optional[datetime] = None


class EngineerInvitationComplete(BaseModel):
    """Schema for finishing invite-based account setup."""
    token: str = Field(..., min_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=8, max_length=255)
    confirm_password: str = Field(..., min_length=8, max_length=255)


class EngineerInvitationResponse(BaseModel):
    """Schema returned after creating or resending an invitation."""
    engineer: EngineerResponse
    delivery_method: str
    delivery_message: str
    invite_url: Optional[str] = None
    expires_at: datetime


# ============================================================================
# Report Schemas (Extended for Frontend)
# ============================================================================

class ReportResponse(BaseModel):
    """Schema for report response with all details"""
    id: str
    tracking_id: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    address: Optional[str] = None
    photos: List[str] = []
    report_photos: List[str] = []
    submission_before_photos: List[str] = []
    submission_after_photos: List[str] = []
    priority: str
    leakage_type: str = "unknown"
    status: str
    utility_id: str
    utility_name: Optional[str] = None
    dma_id: Optional[str] = None
    dma_name: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    team_leader_id: Optional[str] = None
    team_leader_name: Optional[str] = None
    assigned_engineer_id: Optional[str] = None
    assigned_engineer_name: Optional[str] = None
    reporter_name: str
    reporter_phone: str
    notes: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for list of reports"""
    total: int
    items: List[ReportResponse]


class ReportWithDetailsResponse(ReportResponse):
    """Extended report response with additional computed fields"""
    pass
