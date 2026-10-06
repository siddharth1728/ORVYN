"""SQLAlchemy declarative base and common model conventions."""

import os

# Ensure pure Python mode for SQLAlchemy on systems with restrictive DLL policies
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative class for all ORM models."""
    pass
