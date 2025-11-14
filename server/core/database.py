"""
database.py
------------
Handles database engine and session lifecycle.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --------------------------------------------------------------------
# Connection URL — must be set in your environment (.env or Vercel)
# --------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

# --------------------------------------------------------------------
# Engine configuration
# --------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

