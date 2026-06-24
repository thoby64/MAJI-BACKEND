#!/usr/bin/env python
"""
Database seeding script for the current Majiscope hierarchy.

Hierarchy:
    Admin -> Utility -> DMA -> Team -> Engineer
"""

import sys
from datetime import datetime

from app.database.session import SessionLocal
from app.models import (
    DMA,
    DMAManager,
    Engineer,
    EntityStatusEnum,
    Team,
    User,
    Utility,
    UtilityManager,
)
from app.security.auth import hash_password


def seed_db() -> bool:
    """Seed database with initial data."""
    db = SessionLocal()

    print("=" * 60)
    print("Majiscope Database Seeding")
    print("=" * 60)

    try:
        admin = db.query(User).filter(User.email == "admin@majiscope.com").first()
        if admin:
            print("\nAdmin user already exists. Skipping seed.")
            return True

        now = datetime.utcnow()

        print("\nCreating admin user...")
        admin_user = User(
            email="admin@majiscope.com",
            password=hash_password("admin123"),
            name="Admin User",
            phone="+1234567890",
            avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=admin",
            status=EntityStatusEnum.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        db.add(admin_user)
        db.flush()
        print(f"Created admin user: {admin_user.email}")

        print("\nCreating utility...")
        utility = Utility(
            name="City Water Department",
            description="Municipal water supply utility",
            status=EntityStatusEnum.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        db.add(utility)
        db.flush()
        print(f"Created utility: {utility.name}")

        print("\nCreating utility manager...")
        utility_mgr = UtilityManager(
            utility_id=utility.id,
            email="manager@utility.com",
            password=hash_password("manager123"),
            name="John Manager",
            phone="+1111111111",
            status=EntityStatusEnum.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        db.add(utility_mgr)
        db.flush()
        print(f"Created utility manager: {utility_mgr.email}")

        print("\nCreating DMA...")
        dma = DMA(
            utility_id=utility.id,
            name="Downtown DMA",
            description="Downtown water distribution area",
            center_latitude=-3.386,
            center_longitude=36.717,
            status=EntityStatusEnum.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        db.add(dma)
        db.flush()
        print(f"Created DMA: {dma.name}")

        print("\nCreating DMA manager...")
        dma_mgr = DMAManager(
            dma_id=dma.id,
            utility_id=utility.id,
            email="dma.manager@utility.com",
            password=hash_password("dmamanager123"),
            name="Jane DMA Manager",
            phone="+2222222222",
            status=EntityStatusEnum.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        db.add(dma_mgr)
        db.flush()
        print(f"Created DMA manager: {dma_mgr.email}")

        print("\nCreating team...")
        team = Team(
            dma_id=dma.id,
            name="Alpha Team",
            description="Field operations team",
            status=EntityStatusEnum.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        db.add(team)
        db.flush()
        print(f"Created team: {team.name}")

        print("\nCreating team leader...")
        team_leader = Engineer(
            dma_id=dma.id,
            team_id=team.id,
            name="Bob Engineer",
            email="engineer@utility.com",
            password=hash_password("engineer123"),
            phone="+3333333333",
            status=EntityStatusEnum.ACTIVE,
            role="team_leader",
            created_at=now,
            updated_at=now,
        )
        db.add(team_leader)
        db.flush()

        team.leader_id = team_leader.id
        print(f"Created team leader: {team_leader.email}")

        db.commit()

        print("\n" + "=" * 60)
        print("Database seeding completed successfully.")
        print("\nTest Credentials:")
        print("  admin@majiscope.com / admin123")
        print("  manager@utility.com / manager123")
        print("  dma.manager@utility.com / dmamanager123")
        print("  engineer@utility.com / engineer123")
        print("=" * 60)
        return True
    except Exception as exc:
        db.rollback()
        print(f"\nError seeding database: {exc}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = seed_db()
    sys.exit(0 if success else 1)
