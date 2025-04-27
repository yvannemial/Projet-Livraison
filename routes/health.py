from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db

router = APIRouter()

@router.get("/health", tags=["health"])
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring.
    Checks if the application is running and can connect to the database.
    """
    try:
        # Try to execute a simple query to check database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}