#!/usr/bin/env python
"""
Arusha Locations Seeding Script
Add geospatial data for Arusha DMAs and Branches
Usage: python seed_arusha_locations.py
"""

import sys
from datetime import datetime
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import (
    User, Utility, UtilityManager, DMA, DMAManager, 
    Branch, Team, Engineer, EntityStatusEnum
)
from app.security.auth import hash_password

def seed_arusha_locations():
    """Seed database with Arusha-specific locations and geospatial data"""
    db = SessionLocal()
    
    print("=" * 70)
    print("🌍 Majiscope Arusha Locations Seeding")
    print("=" * 70)
    
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.email == "admin@majiscope.com").first()
        if not admin:
            print("\n📝 Creating admin user...")
            admin_user = User(
                email="admin@majiscope.com",
                password=hash_password("admin123"),
                name="Admin User",
                phone="+255700000000",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=admin",
                status=EntityStatusEnum.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(admin_user)
            db.flush()
            print(f"✅ Created admin user: {admin_user.email}")
        
        # Check if Arusha utility already exists
        utility = db.query(Utility).filter(Utility.name == "Arusha Water Utility").first()
        if not utility:
            print("\n📝 Creating Arusha water utility...")
            utility = Utility(
                name="Arusha Water Utility",
                description="Water supply authority for Arusha, Tanzania",
                status=EntityStatusEnum.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(utility)
            db.flush()
            print(f"✅ Created utility: {utility.name}")
        else:
            print(f"\n✓ Utility already exists: {utility.name}")
        
        # Create utility manager if doesn't exist
        utility_mgr = db.query(UtilityManager).filter(
            UtilityManager.email == "arusha.manager@utility.com"
        ).first()
        if not utility_mgr:
            print("\n📝 Creating utility manager...")
            utility_mgr = UtilityManager(
                utility_id=utility.id,
                email="arusha.manager@utility.com",
                password=hash_password("manager123"),
                name="Arusha Manager",
                phone="+255700111111",
                status=EntityStatusEnum.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(utility_mgr)
            db.flush()
            print(f"✅ Created utility manager: {utility_mgr.name}")
        
        # Define Arusha regions with their center coordinates
        # Coordinates are in decimal degrees (latitude, longitude)
        arusha_regions = [
            {
                "name": "Downtown DMA",
                "description": "Central business district and downtown Arusha",
                "center_lat": -3.368,
                "center_lon": 36.679,
                "branches": [
                    {
                        "name": "Downtown Branch",
                        "description": "Central downtown service area",
                        "center_lat": -3.368,
                        "center_lon": 36.679,
                    }
                ]
            },
            {
                "name": "Old Moshi Road DMA",
                "description": "Old Moshi Road and northern residential area",
                "center_lat": -3.386,
                "center_lon": 36.717,
                "branches": [
                    {
                        "name": "Old Moshi Road Branch",
                        "description": "Old Moshi Road corridor",
                        "center_lat": -3.386,
                        "center_lon": 36.717,
                    },
                    {
                        "name": "North Arusha Branch",
                        "description": "Northern residential areas",
                        "center_lat": -3.335,
                        "center_lon": 36.700,
                    }
                ]
            },
            {
                "name": "Industrial DMA",
                "description": "Industrial zone and eastern areas",
                "center_lat": -3.400,
                "center_lon": 36.700,
                "branches": [
                    {
                        "name": "Industrial Branch",
                        "description": "Industrial zone service area",
                        "center_lat": -3.400,
                        "center_lon": 36.700,
                    }
                ]
            },
            {
                "name": "South Arusha DMA",
                "description": "Southern residential and suburban areas",
                "center_lat": -3.395,
                "center_lon": 36.670,
                "branches": [
                    {
                        "name": "South Arusha Branch",
                        "description": "Southern suburbs service area",
                        "center_lat": -3.395,
                        "center_lon": 36.670,
                    }
                ]
            }
        ]
        
        # Create DMAs and branches with geospatial data
        print("\n📝 Creating Arusha DMAs and Branches with geospatial data...")
        for region in arusha_regions:
            # Check if DMA already exists
            dma = db.query(DMA).filter(
                DMA.name == region["name"],
                DMA.utility_id == utility.id
            ).first()
            
            if not dma:
                dma = DMA(
                    utility_id=utility.id,
                    name=region["name"],
                    description=region["description"],
                    center_latitude=region["center_lat"],  # NEW: Geospatial field
                    center_longitude=region["center_lon"],  # NEW: Geospatial field
                    status=EntityStatusEnum.ACTIVE,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(dma)
                db.flush()
                print(f"  ✅ Created DMA: {dma.name}")
                print(f"     └─ Center: ({dma.center_latitude:.3f}, {dma.center_longitude:.3f})")
            else:
                # Update geospatial data if needed
                if dma.center_latitude is None or dma.center_longitude is None:
                    dma.center_latitude = region["center_lat"]
                    dma.center_longitude = region["center_lon"]
                    db.flush()
                    print(f"  ♻️  Updated DMA with geospatial data: {dma.name}")
                else:
                    print(f"  ✓ DMA already exists: {dma.name}")
            
            # Create DMA manager if doesn't exist
            dma_mgr = db.query(DMAManager).filter(
                DMAManager.dma_id == dma.id
            ).first()
            if not dma_mgr:
                dma_mgr = DMAManager(
                    dma_id=dma.id,
                    utility_id=utility.id,
                    email=f"dma.{region['name'].lower().replace(' ', '.')}@utility.com",
                    password=hash_password("dmamanager123"),
                    name=f"{region['name']} Manager",
                    phone="+255700222222",
                    status=EntityStatusEnum.ACTIVE,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(dma_mgr)
                db.flush()
                print(f"     └─ DMA Manager: {dma_mgr.name}")
            
            # Create branches within the DMA
            for branch_data in region["branches"]:
                branch = db.query(Branch).filter(
                    Branch.name == branch_data["name"],
                    Branch.dma_id == dma.id
                ).first()
                
                if not branch:
                    branch = Branch(
                        utility_id=utility.id,
                        dma_id=dma.id,
                        name=branch_data["name"],
                        description=branch_data["description"],
                        center_latitude=branch_data["center_lat"],  # NEW: Geospatial field
                        center_longitude=branch_data["center_lon"],  # NEW: Geospatial field
                        status=EntityStatusEnum.ACTIVE,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(branch)
                    db.flush()
                    print(f"     └─ Branch: {branch.name}")
                    print(f"        └─ Center: ({branch.center_latitude:.3f}, {branch.center_longitude:.3f})")
                else:
                    # Update geospatial data if needed
                    if branch.center_latitude is None or branch.center_longitude is None:
                        branch.center_latitude = branch_data["center_lat"]
                        branch.center_longitude = branch_data["center_lon"]
                        db.flush()
                        print(f"     └─ ♻️  Updated branch with geospatial data: {branch.name}")
                    else:
                        print(f"     └─ ✓ Branch already exists: {branch.name}")
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 70)
        print("✅ Seeding completed successfully!")
        print("=" * 70)
        print("\n📊 Summary:")
        print(f"   ├─ Utility: Arusha Water Utility")
        print(f"   ├─ DMAs created: {db.query(DMA).filter(DMA.utility_id == utility.id).count()}")
        print(f"   └─ Branches created: {db.query(Branch).filter(Branch.utility_id == utility.id).count()}")
        print("\n🎯 Reports submitted in Arusha will now be assigned to the nearest")
        print("   branch based on geospatial coordinates!")
        print("\n" + "=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = seed_arusha_locations()
    sys.exit(0 if success else 1)
