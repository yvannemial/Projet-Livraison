from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from db import get_db
from db.models import MenuCategory, Menu
from db.schemas import MenuCategoryCreate, MenuCategory as MenuCategorySchema, MenuCategoryUpdate, Menu as MenuSchema

router = APIRouter()


@router.post("/menu-categories", response_model=MenuCategorySchema, status_code=status.HTTP_201_CREATED)
def create_menu_category(menu_category: MenuCategoryCreate, db: Session = Depends(get_db)):
    """Create a new menu category"""
    db_menu_category = MenuCategory(**menu_category.model_dump())
    db.add(db_menu_category)
    db.commit()
    db.refresh(db_menu_category)
    return db_menu_category


@router.get("/menu-categories", response_model=List[MenuCategorySchema])
def list_menu_categories(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    db: Session = Depends(get_db)
):
    """Get all menu categories"""
    menu_categories = db.query(MenuCategory).offset(skip).limit(limit).all()
    return menu_categories


@router.get("/menu-categories/{category_id}", response_model=MenuCategorySchema)
def get_menu_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific menu category by ID"""
    menu_category = db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
    if menu_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu category not found"
        )
    return menu_category


@router.put("/menu-categories/{category_id}", response_model=MenuCategorySchema)
def update_menu_category(
    category_id: int,
    menu_category_update: MenuCategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update a menu category"""
    db_menu_category = db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
    if db_menu_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu category not found"
        )

    # Update only provided fields
    update_data = menu_category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_menu_category, key, value)

    db.commit()
    db.refresh(db_menu_category)
    return db_menu_category


@router.delete("/menu-categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a menu category"""
    db_menu_category = db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
    if db_menu_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu category not found"
        )

    # Check if there are any menus using this category
    menus_with_category = db.query(Menu).filter(Menu.categories.any(MenuCategory.id == category_id)).count()
    if menus_with_category > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: {menus_with_category} menu items are using this category"
        )

    db.delete(db_menu_category)
    db.commit()
    return None


@router.get("/menu-categories/{category_id}/menus", response_model=List[MenuSchema])
def get_menus_by_category(
    category_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    db: Session = Depends(get_db)
):
    """Get all menus for a specific category"""
    # Verify category exists
    category = db.query(MenuCategory).filter(MenuCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu category not found"
        )

    menus = db.query(Menu).filter(Menu.categories.any(MenuCategory.id == category_id)).offset(skip).limit(limit).all()
    return menus
