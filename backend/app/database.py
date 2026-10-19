import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env
load_dotenv()

# Require an explicit database URL; never fall back to hard-coded credentials.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or not DATABASE_URL.strip():
    raise RuntimeError(
        "DATABASE_URL is required. Configure it in the environment or backend/.env."
    )

# SQLAlchemy engine initialization
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model
Base = declarative_base()
