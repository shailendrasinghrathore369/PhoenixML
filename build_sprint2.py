import os
from pathlib import Path

base_path = Path("C:/Users/Shailendra Singh/Videos/Study Material/PhoenixML/backend")

# 1. Update requirements.txt
req_path = base_path / "requirements.txt"
with open(req_path, "a") as f:
    f.write("passlib[bcrypt]>=1.7.4\n")
    f.write("email-validator>=2.1.0\n")
    f.write("pytest>=8.0.0\n")
    f.write("httpx>=0.26.0\n")

# 2. Create models/user.py
user_model = """from datetime import datetime
import uuid
from typing import Optional
import enum
from sqlalchemy import String, Boolean, DateTime, Enum, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
"""
with open(base_path / "app/models/user.py", "w") as f:
    f.write(user_model)

# 3. Update app/db/base.py
base_content = """from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
"""
with open(base_path / "app/db/base.py", "w") as f:
    f.write(base_content)

# 4. Create auth/schemas.py
schemas = """from pydantic import BaseModel, EmailStr, Field, ConfigDict
import uuid
from datetime import datetime
from app.models.user import UserRole

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserRegisterResponse(BaseModel):
    message: str
    user: UserResponse
"""
with open(base_path / "app/auth/schemas.py", "w") as f:
    f.write(schemas)

# 5. Create auth/security.py
security = """from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
"""
with open(base_path / "app/auth/security.py", "w") as f:
    f.write(security)

# 6. Create auth/repository.py
repo = """from sqlalchemy.orm import Session
from app.models.user import User
from app.auth.schemas import UserCreate
from app.auth.security import get_password_hash
from typing import Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, user_in: UserCreate) -> User:
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
"""
with open(base_path / "app/auth/repository.py", "w") as f:
    f.write(repo)

# 7. Create auth/service.py
service = """from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate, UserResponse
from app.db.dependencies import get_db

class AuthService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = UserRepository(db)

    def register_user(self, user_in: UserCreate) -> dict:
        if self.repo.get_user_by_username(user_in.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered"
            )
        if self.repo.get_user_by_email(user_in.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        user = self.repo.create_user(user_in)
        return {
            "message": "User registered successfully",
            "user": user
        }
"""
with open(base_path / "app/auth/service.py", "w") as f:
    f.write(service)

# 8. Create auth/router.py
router = """from fastapi import APIRouter, Depends, status
from app.auth.schemas import UserCreate, UserRegisterResponse
from app.auth.service import AuthService

router = APIRouter()

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, auth_service: AuthService = Depends()):
    return auth_service.register_user(user_in)
"""
with open(base_path / "app/auth/router.py", "w") as f:
    f.write(router)

# 9. Modify main.py
main_content = """import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
from app.auth.router import router as auth_router

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up PhoenixML backend...")
    yield
    logger.info("Shutting down PhoenixML backend...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
        debug=settings.DEBUG
    )

    register_exception_handlers(app)

    api_router = APIRouter()
    
    @api_router.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "project": settings.PROJECT_NAME}
        
    app.include_router(api_router, prefix="/api")
    
    # Register auth router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    
    return app

app = create_app()
"""
with open(base_path / "app/main.py", "w") as f:
    f.write(main_content)

# 10. Tests
tests_dir = base_path / "tests"
tests_dir.mkdir(exist_ok=True)
(tests_dir / "__init__.py").touch()

conftest = """import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.base import Base
from app.db.dependencies import get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def cleanup_database():
    # Clean up the DB before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
"""
with open(tests_dir / "conftest.py", "w") as f:
    f.write(conftest)

test_auth = """import pytest
from fastapi.testclient import TestClient

def test_successful_registration(client: TestClient):
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert "user" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["role"] == "user"
    assert "id" in data["user"]
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]

def test_duplicate_username(client: TestClient):
    # First user
    client.post("/api/auth/register", json={
        "username": "dupuser",
        "email": "first@example.com",
        "password": "password123"
    })
    # Second user with same username
    response = client.post("/api/auth/register", json={
        "username": "dupuser",
        "email": "second@example.com",
        "password": "password123"
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already registered"

def test_duplicate_email(client: TestClient):
    # First user
    client.post("/api/auth/register", json={
        "username": "user1",
        "email": "dup@example.com",
        "password": "password123"
    })
    # Second user with same email
    response = client.post("/api/auth/register", json={
        "username": "user2",
        "email": "dup@example.com",
        "password": "password123"
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

def test_invalid_email(client: TestClient):
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "invalid-email",
        "password": "password123"
    })
    assert response.status_code == 422

def test_short_password(client: TestClient):
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "short"
    })
    assert response.status_code == 422
"""
with open(tests_dir / "test_auth.py", "w") as f:
    f.write(test_auth)
