from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.settings import settings

# Create SQLAlchemy engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency function to get a database session.
    Used in FastAPI dependency injection system.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()