from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from db import get_db
from db.models import User as UserModel
from db.schemas import UserCreate, TokenData, UserLogin, User
from utils.auth import verify_password, get_password_hash, create_access_token

router = APIRouter()


@router.post("/register", response_model=TokenData)
def register(client: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        existing_user = db.query(UserModel).filter(UserModel.email == client.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user with hashed password
        hashed_password = get_password_hash(client.password)
        db_client = UserModel(
            first_name=client.first_name,
            last_name=client.last_name,
            email=client.email,
            phone_number=client.phone_number,
            address=client.address or "",
            password_hash=hashed_password
        )

        db.add(db_client)
        db.commit()
        db.refresh(db_client)

        # Create access token
        access_token = create_access_token(
            data={"sub": db_client.id, "email": db_client.email},
        )

        return TokenData(access_token=access_token)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", response_model=TokenData)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    try:
        # Find user by email
        user = db.query(UserModel).filter(UserModel.email == user_credentials.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
        )

        return TokenData(access_token=access_token)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
