"""
Image Service
Handles image validation, compression, and storage
"""

import io
from PIL import Image
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_DIMENSION = 4096
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
COMPRESSION_QUALITY = 85


class ImageValidationError(Exception):
    """Raised when image validation fails"""
    pass


def validate_image(file_data: bytes, file_type: str) -> Tuple[int, int]:
    """
    Validate image and return dimensions
    
    Args:
        file_data: Binary image data
        file_type: MIME type (e.g., 'image/jpeg')
    
    Returns:
        Tuple of (width, height)
    
    Raises:
        ImageValidationError: If image is invalid
    """
    # Check file size
    if len(file_data) > MAX_IMAGE_SIZE:
        raise ImageValidationError(
            f"Image too large: {len(file_data) / 1024 / 1024:.1f}MB (max {MAX_IMAGE_SIZE / 1024 / 1024:.1f}MB)"
        )
    
    # Check MIME type
    if file_type not in ALLOWED_MIME_TYPES:
        raise ImageValidationError(f"Invalid image type: {file_type}")
    
    try:
        # Open and validate image
        img = Image.open(io.BytesIO(file_data))
        img.verify()
        
        # Reopen (verify() closes the file)
        img = Image.open(io.BytesIO(file_data))
        
        width, height = img.size
        
        # Check dimensions
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise ImageValidationError(
                f"Image dimensions too large: {width}x{height} (max {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION})"
            )
        
        logger.info(f"✅ Image validated: {width}x{height}, {len(file_data) / 1024:.1f}KB, type={file_type}")
        return width, height
        
    except ImageValidationError:
        raise
    except Exception as e:
        raise ImageValidationError(f"Invalid image file: {str(e)}")


def compress_image_if_needed(
    file_data: bytes,
    file_type: str,
    max_width: int = 1920,
    max_height: int = 1920,
) -> Tuple[bytes, str, int, int]:
    """
    Compress image if needed while maintaining aspect ratio
    
    Args:
        file_data: Binary image data
        file_type: MIME type
        max_width: Maximum width
        max_height: Maximum height
    
    Returns:
        Tuple of (compressed_data, mime_type, width, height)
    """
    try:
        img = Image.open(io.BytesIO(file_data))
        original_size = len(file_data)
        width, height = img.size
        
        # Check if compression needed
        if width > max_width or height > max_height:
            # Calculate scaling factor
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Resize image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to appropriate format for compression
            output_format = "JPEG" if file_type == "image/jpeg" else "PNG"
            
            # Compress
            output = io.BytesIO()
            img.save(output, format=output_format, quality=COMPRESSION_QUALITY, optimize=True)
            compressed_data = output.getvalue()
            
            compression_ratio = (1 - len(compressed_data) / original_size) * 100
            logger.info(
                f"✅ Image compressed: {width}x{height} → {new_width}x{new_height}, "
                f"{original_size / 1024:.1f}KB → {len(compressed_data) / 1024:.1f}KB ({compression_ratio:.1f}% reduction)"
            )
            
            return compressed_data, file_type, new_width, new_height
        
        logger.info(f"Image compression skipped: Already within limits ({width}x{height})")
        return file_data, file_type, width, height
        
    except Exception as e:
        logger.error(f"Compression error: {str(e)}")
        # Return original if compression fails
        return file_data, file_type, width, height


def get_image_mime_type(file_extension: str) -> str:
    """Get MIME type from file extension"""
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
    }
    return mime_types.get(file_extension.lower(), 'image/jpeg')
