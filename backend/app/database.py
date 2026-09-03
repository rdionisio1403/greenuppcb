import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env
load_dotenv()

# Database connection URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://greenupcb:1234@localhost:5432/greenupcb_lis"
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
