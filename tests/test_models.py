"""
Database Tests
Tests for database models and ORM operations
"""

import pytest
from sqlalchemy.orm import Session
from app.models import User, Utility, DMA, Branch, Team, Engineer
from app.security.auth import hash_password
from app.constants.enums import EntityStatus


class TestUserModel:
    """User model tests"""
    
    def test_create_user(self, db: Session):
        """Test creating user"""
        user = User(
            email="model@example.com",
            first_name="Model",
            last_name="Test",
            password_hash=hash_password("password123"),
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.id
        assert user.email == "model@example.com"
        assert user.created_at
    
    def test_user_relationships(self, db: Session):
        """Test user relationships"""
        user = User(
            email="relationship@example.com",
            first_name="Test",
            last_name="User",
            password_hash=hash_password("password123"),
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.activity_logs is not None or user.activity_logs == []
        assert user.notifications is not None or user.notifications == []


class TestUtilityHierarchy:
    """Utility hierarchy model tests"""
    
    def test_utility_creation(self, db: Session):
        """Test creating utility"""
        utility = Utility(
            name="Test Utility",
            description="Test",
            status=EntityStatus.ACTIVE,
        )
        
        db.add(utility)
        db.commit()
        db.refresh(utility)
        
        assert utility.id
        assert utility.name == "Test Utility"
    
    def test_dma_creation_with_utility(self, db: Session):
        """Test creating DMA with utility relationship"""
        utility = Utility(name="Utility", status=EntityStatus.ACTIVE)
        db.add(utility)
        db.commit()
        db.refresh(utility)
        
        dma = DMA(
            utility_id=utility.id,
            name="Test DMA",
            status=EntityStatus.ACTIVE,
        )
        
        db.add(dma)
        db.commit()
        db.refresh(dma)
        
        assert dma.id
        assert dma.utility_id == utility.id
    
    def test_branch_creation_with_dma(self, db: Session):
        """Test creating branch with DMA relationship"""
        utility = Utility(name="Utility", status=EntityStatus.ACTIVE)
        db.add(utility)
        db.commit()
        
        dma = DMA(
            utility_id=utility.id,
            name="DMA",
            status=EntityStatus.ACTIVE,
        )
        db.add(dma)
        db.commit()
        db.refresh(dma)
        
        branch = Branch(
            dma_id=dma.id,
            name="Test Branch",
            status=EntityStatus.ACTIVE,
        )
        
        db.add(branch)
        db.commit()
        db.refresh(branch)
        
        assert branch.id
        assert branch.dma_id == dma.id


class TestTeamStructure:
    """Team and engineer structure tests"""
    
    def test_team_creation(self, db: Session):
        """Test creating team"""
        utility = Utility(name="Utility", status=EntityStatus.ACTIVE)
        db.add(utility)
        db.commit()
        
        dma = DMA(utility_id=utility.id, name="DMA", status=EntityStatus.ACTIVE)
        db.add(dma)
        db.commit()
        
        branch = Branch(dma_id=dma.id, name="Branch", status=EntityStatus.ACTIVE)
        db.add(branch)
        db.commit()
        db.refresh(branch)
        
        team = Team(
            branch_id=branch.id,
            name="Test Team",
            status=EntityStatus.ACTIVE,
        )
        
        db.add(team)
        db.commit()
        db.refresh(team)
        
        assert team.id
        assert team.branch_id == branch.id
    
    def test_engineer_assignment(self, db: Session):
        """Test assigning engineer to team"""
        # Create user
        user = User(
            email="engineer@example.com",
            first_name="Engineer",
            last_name="User",
            password_hash=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create team structure
        utility = Utility(name="Utility", status=EntityStatus.ACTIVE)
        db.add(utility)
        db.commit()
        
        dma = DMA(utility_id=utility.id, name="DMA", status=EntityStatus.ACTIVE)
        db.add(dma)
        db.commit()
        
        branch = Branch(dma_id=dma.id, name="Branch", status=EntityStatus.ACTIVE)
        db.add(branch)
        db.commit()
        
        team = Team(branch_id=branch.id, name="Team", status=EntityStatus.ACTIVE)
        db.add(team)
        db.commit()
        db.refresh(team)
        
        # Assign engineer
        engineer = Engineer(
            user_id=user.id,
            team_id=team.id,
            specialization="Water Systems",
            status=EntityStatus.ACTIVE,
        )
        
        db.add(engineer)
        db.commit()
        db.refresh(engineer)
        
        assert engineer.id
        assert engineer.user_id == user.id
        assert engineer.team_id == team.id
