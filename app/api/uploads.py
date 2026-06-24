"""
Media Upload Routes
API endpoints for image and video upload and retrieval.
"""

import logging
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import ImageUpload, Report
from app.models.uploads import ImageTypeEnum
from app.security.dependencies import CurrentUser, get_current_user
from app.services.image_service import compress_image_if_needed, validate_image

logger = logging.getLogger(__name__)

uploads_router = APIRouter(prefix="/api/uploads", tags=["uploads"])

MAX_VIDEO_SIZE = 25 * 1024 * 1024  # 25MB


def _build_upload_response(image_upload: ImageUpload):
    return {
        "id": image_upload.id,
        "fileName": image_upload.file_name,
        "fileSize": image_upload.file_size,
        "width": image_upload.width,
        "height": image_upload.height,
        "mimeType": image_upload.mime_type,
        "imageType": image_upload.image_type,
        "createdAt": image_upload.created_at,
        "downloadUrl": f"/api/uploads/{image_upload.id}",
    }


def _validate_media_upload(file: UploadFile, file_data: bytes) -> Tuple[bytes, str, Optional[int], Optional[int]]:
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is missing a content type",
        )

    if file.content_type.startswith("image/"):
        try:
            validate_image(file_data, file.content_type)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image validation failed: {str(exc)}",
            )

        compressed_data, mime_type, final_width, final_height = compress_image_if_needed(
            file_data,
            file.content_type,
            max_width=1920,
            max_height=1920,
        )
        return compressed_data, mime_type, final_width, final_height

    if file.content_type.startswith("video/"):
        if len(file_data) > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video too large: {len(file_data) / 1024 / 1024:.1f}MB (max {MAX_VIDEO_SIZE / 1024 / 1024:.1f}MB)",
            )
        return file_data, file.content_type, None, None

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="File must be an image or video",
    )


@uploads_router.post("", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    report_id: str = Form(None),
    image_type: str = Form("report"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an image or video file and store it in PostgreSQL.
    """
    try:
        file_data = await file.read()
        stored_data, mime_type, final_width, final_height = _validate_media_upload(file, file_data)

        if report_id:
            report = db.query(Report).filter(Report.id == report_id).first()
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report not found",
                )

        image_upload = ImageUpload(
            file_data=stored_data,
            file_name=file.filename,
            file_type=file.content_type,
            file_size=len(stored_data),
            mime_type=mime_type,
            image_type=image_type,
            report_id=report_id,
            user_id=current_user.id if current_user.user_type == "user" else None,
            engineer_id=current_user.id if current_user.user_type == "engineer" else None,
            width=final_width,
            height=final_height,
        )

        db.add(image_upload)
        db.commit()
        db.refresh(image_upload)

        logger.info("Media uploaded: %s (%s)", image_upload.id, mime_type)
        return _build_upload_response(image_upload)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Media upload error: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Media upload failed",
        )


@uploads_router.post("/public", status_code=status.HTTP_201_CREATED)
async def upload_public_image(
    file: UploadFile = File(...),
    image_type: str = Form("report"),
    db: Session = Depends(get_db),
):
    """Anonymous/public image or video upload for the public reporting app."""
    try:
        file_data = await file.read()
        stored_data, mime_type, final_width, final_height = _validate_media_upload(file, file_data)

        image_upload = ImageUpload(
            file_data=stored_data,
            file_name=file.filename,
            file_type=file.content_type,
            file_size=len(stored_data),
            mime_type=mime_type,
            image_type=image_type,
            report_id=None,
            user_id=None,
            engineer_id=None,
            width=final_width,
            height=final_height,
        )

        db.add(image_upload)
        db.commit()
        db.refresh(image_upload)

        logger.info("Public media uploaded: %s (%s)", image_upload.id, mime_type)
        return _build_upload_response(image_upload)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Public media upload error: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Public media upload failed",
        )


@uploads_router.get("/{image_id}")
async def download_image(image_id: str, db: Session = Depends(get_db)):
    """
    Download/retrieve a stored media payload.
    """
    try:
        image = db.query(ImageUpload).filter(ImageUpload.id == image_id).first()

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )

        return {
            "id": image.id,
            "fileName": image.file_name,
            "mimeType": image.mime_type,
            "data": image.file_data.hex(),
            "width": image.width,
            "height": image.height,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Media download error: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image download failed",
        )


@uploads_router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an uploaded media file (auth required).
    """
    try:
        image = db.query(ImageUpload).filter(ImageUpload.id == image_id).first()

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )

        if current_user.user_type == "engineer" and image.engineer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this image",
            )

        db.delete(image)
        db.commit()

        logger.info("Media deleted: %s", image_id)
        return {"message": "Image deleted successfully"}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Media deletion error: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image deletion failed",
        )
