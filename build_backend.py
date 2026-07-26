import os
from pathlib import Path

# Base Path
base_path = Path("C:/Users/Shailendra Singh/Videos/Study Material/PhoenixML/backend")
base_path.mkdir(parents=True, exist_ok=True)

# Directory structure
dirs = [
    "app",
    "app/auth",
    "app/users",
    "app/models",
    "app/monitoring",
    "app/decisions",
    "app/dashboard",
    "app/core",
    "app/db",
    "app/shared",
    "app/tests",
    "app/api",
    "alembic",
    "alembic/versions"
]

for d in dirs:
    (base_path / d).mkdir(parents=True, exist_ok=True)
    # create __init__.py in all app subdirectories
    if d.startswith("app/") and "tests" not in d:
        (base_path / d / "__init__.py").touch()

(base_path / "app" / "__init__.py").touch()

files_content = {
    "requirements.txt": """fastapi>=0.109.0
uvicorn>=0.27.0
sqlalchemy>=2.0.25
alembic>=1.13.1
psycopg2-binary>=2.9.9
pydantic>=2.6.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.1
""",
    ".env.example": """PROJECT_NAME="PhoenixML"
DEBUG=True
DATABASE_URL="postgresql://phoenix_user:phoenix_password@db:5432/phoenixml"
SECRET_KEY="your-super-secret-key-change-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM="HS256"
""",
    ".env": """PROJECT_NAME="PhoenixML"
DEBUG=True
DATABASE_URL="postgresql://phoenix_user:phoenix_password@localhost:5432/phoenixml"
SECRET_KEY="your-super-secret-key-change-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM="HS256"
""",
    "Dockerfile": """FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \\
    && apt-get install -y --no-install-recommends gcc libpq-dev \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \\
    && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    "docker-compose.yml": """version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: phoenixml_db
    environment:
      POSTGRES_USER: phoenix_user
      POSTGRES_PASSWORD: phoenix_password
      POSTGRES_DB: phoenixml
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U phoenix_user -d phoenixml"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: .
    container_name: phoenixml_backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://phoenix_user:phoenix_password@db:5432/phoenixml
      - DEBUG=True
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
""",
    "app/core/config.py": """from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "PhoenixML"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Authentication
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

settings = Settings()
""",
    "app/core/logging.py": """import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings

def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "phoenixml.log"
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(log_format)
    
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
""",
    "app/core/exceptions.py": """from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, global_exception_handler)
""",
    "app/db/base_class.py": """from sqlalchemy.orm import DeclarativeBase
from typing import Any

class Base(DeclarativeBase):
    id: Any
    __name__: str
""",
    "app/db/database.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
""",
    "app/db/dependencies.py": """from typing import Generator
from sqlalchemy.orm import Session
from app.db.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
    "app/db/base.py": """from app.db.base_class import Base  # noqa
""",
    "app/main.py": """import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers

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
    
    return app

app = create_app()
""",
    "alembic.ini": """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""",
    "alembic/env.py": """import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""",
    "alembic/script.py.mako": '\"\"\"${message}\\n\\nRevision ID: ${up_revision}\\nRevises: ${down_revision | comma,n}\\nCreate Date: ${create_date}\\n\\n\"\"\"\\nfrom typing import Sequence, Union\\n\\nfrom alembic import op\\nimport sqlalchemy as sa\\n${imports if imports else ""}\\n\\n# revision identifiers, used by Alembic.\\nrevision: str = ${repr(up_revision)}\\ndown_revision: Union[str, None] = ${repr(down_revision)}\\nbranch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}\\ndepends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}\\n\\n\\ndef upgrade() -> None:\\n    ${upgrades if upgrades else "pass"}\\n\\n\\ndef downgrade() -> None:\\n    ${downgrades if downgrades else "pass"}\\n'
}

for file_path, content in files_content.items():
    with open(base_path / file_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Files created successfully.")
