from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from db import get_db
from db.models import Comment, Menu, User
from db.schemas import CommentCreate, Comment as CommentSchema, CommentUpdate

router = APIRouter()


@router.post("/comments", response_model=CommentSchema, status_code=status.HTTP_201_CREATED)
def create_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    # Verify menu exists
    menu = db.query(Menu).filter(Menu.id == comment.menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    # Verify user exists
    user = db.query(User).filter(User.id == comment.client_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate rating range (1-5)
    if not 1 <= comment.rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )

    db_comment = Comment(**comment.model_dump())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


@router.get("/comments", response_model=List[CommentSchema])
def list_comments(
        menu_id: int | None = None,
        client_id: int | None = None,
        rating: int | None = Query(None, ge=1, le=5),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100),
        db: Session = Depends(get_db)
):
    query = db.query(Comment)

    if menu_id:
        query = query.filter(Comment.menu_id == menu_id)
    if client_id:
        query = query.filter(Comment.client_id == client_id)
    if rating:
        query = query.filter(Comment.rating == rating)

    comments = query.offset(skip).limit(limit).all()
    return comments


@router.get("/comments/{comment_id}", response_model=CommentSchema)
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    return comment


@router.put("/comments/{comment_id}", response_model=CommentSchema)
def update_comment(
        comment_id: int,
        comment_update: CommentUpdate,
        db: Session = Depends(get_db)
):
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Validate rating if provided
    if comment_update.rating is not None and not 1 <= comment_update.rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )

    # Update only provided fields
    update_data = comment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_comment, key, value)

    db.commit()
    db.refresh(db_comment)
    return db_comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    db.delete(db_comment)
    db.commit()
    return None


@router.get("/menus/{menu_id}/comments", response_model=List[CommentSchema])
def get_menu_comments(
        menu_id: int,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100),
        min_rating: int = Query(None, ge=1, le=5),
        db: Session = Depends(get_db)
):
    # Verify menu exists
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    query = db.query(Comment).filter(Comment.menu_id == menu_id)

    if min_rating:
        query = query.filter(Comment.rating >= min_rating)

    comments = query.offset(skip).limit(limit).all()
    return comments


@router.get("/menus/{menu_id}/rating", response_model=dict)
def get_menu_rating(menu_id: int, db: Session = Depends(get_db)):
    # Verify menu exists
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    from sqlalchemy import func
    result = db.query(
        func.avg(Comment.rating).label("average_rating"),
        func.count(Comment.id).label("total_reviews")
    ).filter(Comment.menu_id == menu_id).first()

    return {
        "menu_id": menu_id,
        "average_rating": float(result.average_rating) if result.average_rating else 0.0,
        "total_reviews": result.total_reviews
    }
