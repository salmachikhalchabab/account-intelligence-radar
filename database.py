import os

from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Models ──

class User(Base):
    __tablename__ = "users"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email        = Column(String, unique=True, nullable=False, index=True)
    username     = Column(String, unique=True, nullable=False)
    password     = Column(String, nullable=False)  # bcrypt hash
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="owner", cascade="all, delete")
    jobs    = relationship("Job", back_populates="owner", cascade="all, delete")


class Report(Base):
    __tablename__ = "reports"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id      = Column(String, ForeignKey("users.id"), nullable=False)
    company      = Column(String, nullable=False)
    filename     = Column(String, nullable=False)
    json_path    = Column(String)
    md_path      = Column(String)
    data         = Column(Text)   # JSON string
    created_at   = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="reports")


class Job(Base):
    __tablename__ = "jobs"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id      = Column(String, ForeignKey("users.id"), nullable=False)
    mode         = Column(String)       # "company" or "geography"
    status       = Column(String, default="pending")   # pending/running/done/error
    input_data   = Column(Text)         # JSON string of the request
    logs         = Column(Text)         # JSON array of log strings
    result       = Column(Text)         # JSON result
    error        = Column(String)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="jobs")


# ── Helpers ──

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
