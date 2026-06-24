"""
ImageUpload Model
SQLAlchemy ORM model for storing uploaded images in PostgreSQL
"""

from sqlalchemy import Column, String, LargeBinary, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.base import Base


class ImageTypeEnum(str, enum.Enum):
    """Image type enumeration"""
    REPORT = "report"
    SUBMISSION_BEFORE = "submission_before"
    SUBMISSION_AFTER = "submission_after"
    PROFILE = "profile"


class ImageUpload(Base):
    """Uploaded Image - Stores image files in PostgreSQL"""
    
    __tablename__ = "image_upload"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    file_data = Column(LargeBinary, nullable=False)  # Binary image data
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # e.g., 'image/jpeg', 'image/png'
    file_size = Column(Integer, nullable=False)  # Size in bytes
    image_type = Column(SQLEnum(ImageTypeEnum), default=ImageTypeEnum.REPORT, nullable=False)
    
    # Foreign keys
    report_id = Column(String(36), ForeignKey("report.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    engineer_id = Column(String(36), ForeignKey("engineer.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    mime_type = Column(String(50), nullable=False, default="image/jpeg")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    report = relationship("Report", back_populates="images", foreign_keys=[report_id])
    user = relationship("User", foreign_keys=[user_id])
    engineer = relationship("Engineer", foreign_keys=[engineer_id])
