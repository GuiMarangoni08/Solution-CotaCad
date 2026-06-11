import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from db.database import Base, get_db
from main import app
from db.models import User
from core.security import get_password_hash


@pytest.fixture(scope="function")
def test_db():
    """Cria banco de dados em memória para testes"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session):
    """Cria usuário de teste"""
    user = User(
        email="testuser@example.com",
        password_hash=get_password_hash("testpass123"),
        is_admin=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def admin_user(test_db: Session):
    """Cria usuário admin de teste"""
    user = User(
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        is_admin=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user
