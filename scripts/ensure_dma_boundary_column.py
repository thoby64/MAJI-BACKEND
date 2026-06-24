#!/usr/bin/env python3
"""
One-off helper: add dma.boundary_geojson if missing.

Usage (from WEB-BASED/Backend):
  set DATABASE_URL=postgresql+psycopg://...
  python scripts/ensure_dma_boundary_column.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database.session import engine
from app.services.database_migrations import _migrate_dma_boundary_columns


def main() -> None:
    _migrate_dma_boundary_columns(engine)
    print("Done. dma.boundary_geojson is present (or was already added).")


if __name__ == "__main__":
    main()
