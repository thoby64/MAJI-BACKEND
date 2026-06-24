"""
SQLAlchemy Base Model
All models inherit from this base class
"""

from sqlalchemy.orm import declarative_base

# Create declarative base for all models
Base = declarative_base()

__all__ = ["Base"]
