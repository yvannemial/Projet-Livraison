from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from db import get_db
from db.models import Supplement, Menu
from db.schemas import SupplementCreate, Supplement as SupplementSchema, SupplementUpdate

router = APIRouter()


@router.post("/supplements", response_model=SupplementSchema, status_code=status.HTTP_201_CREATED)
def create_supplement(supplement: SupplementCreate, db: Session = Depends(get_db)):
    """Create a new supplement"""
    db_supplement = Supplement(**supplement.model_dump())
    db.add(db_supplement)
    db.commit()
    db.refresh(db_supplement)
    return db_supplement


@router.get("/supplements", response_model=List[SupplementSchema])
def list_supplements(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    db: Session = Depends(get_db)
):
    """List all supplements"""
    supplements = db.query(Supplement).offset(skip).limit(limit).all()
    return supplements


@router.get("/supplements/{supplement_id}", response_model=SupplementSchema)
def get_supplement(supplement_id: int, db: Session = Depends(get_db)):
    """Get a specific supplement by ID"""
    supplement = db.query(Supplement).filter(Supplement.id == supplement_id).first()
    if supplement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplement not found"
        )
    return supplement


@router.put("/supplements/{supplement_id}", response_model=SupplementSchema)
def update_supplement(
    supplement_id: int,
    supplement_update: SupplementUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific supplement"""
    db_supplement = db.query(Supplement).filter(Supplement.id == supplement_id).first()
    if db_supplement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplement not found"
        )

    # Get update data excluding unset fields
    update_data = supplement_update.model_dump(exclude_unset=True)

    # Update fields
    for key, value in update_data.items():
        setattr(db_supplement, key, value)

    db.commit()
    db.refresh(db_supplement)
    return db_supplement


@router.delete("/supplements/{supplement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplement(supplement_id: int, db: Session = Depends(get_db)):
    """Delete a specific supplement"""
    db_supplement = db.query(Supplement).filter(Supplement.id == supplement_id).first()
    if db_supplement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplement not found"
        )

    # Check if the supplement is associated with any menus
    if db_supplement.menus:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete supplement that is in use by menus"
        )

    db.delete(db_supplement)
    db.commit()
    return None


@router.get("/menus/{menu_id}/supplements", response_model=List[SupplementSchema])
def get_menu_supplements(
    menu_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    db: Session = Depends(get_db)
):
    """Get all supplements for a specific menu"""
    # Verify menu exists
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if menu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )

    # Get supplements for the menu
    supplements = menu.supplements[skip:skip+limit]
    return supplements