"""
Tracking ID Utility
Generate unique tracking IDs for reports
"""

from datetime import datetime


def generate_tracking_id() -> str:
    """
    Generate a unique tracking ID for reports
    Format: HN-YEAR-RANDOMXXXX
    
    Example: HN-2026-ABC1234
    """
    year = datetime.now().year
    random_str = datetime.now().strftime("%H%M%S")  # HHMMSS
    sequence = datetime.now().microsecond // 1000   # milliseconds
    
    return f"HN-{year}-{random_str}{sequence:03d}"
