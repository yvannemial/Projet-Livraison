from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, outerjoin
from typing import List, Dict, Any

from db import get_db
from db.models import Menu, Restaurant, MenuCategory, Comment, Supplement
from db.schemas import MenuCreate, Menu as MenuSchema, MenuUpdate

router = APIRouter()

MINIMUM_PREP_TIME = 1  # minimum 1 minute


def calculate_average_ratings(db: Session, menu_ids: List[int]) -> Dict[int, float]:
    """
    Calculate average ratings for a list of menu IDs
    Returns a dictionary mapping menu_id to average_rating
    """
    if not menu_ids:
        return {}

    # Query to calculate average rating for each menu in the list
    ratings = (
        db.query(
            Comment.menu_id,
            func.avg(Comment.rating).label("average_rating")
        )
        .filter(Comment.menu_id.in_(menu_ids))
        .group_by(Comment.menu_id)
        .all()
    )

    # Convert to dictionary for easy lookup
    return {rating.menu_id: float(rating.average_rating) for rating in ratings}


@router.post("/menus", response_model=MenuSchema, status_code=status.HTTP_201_CREATED)
def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    if not menu.preparation_time >= MINIMUM_PREP_TIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preparation time must be at least {MINIMUM_PREP_TIME} minute"
        )

    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.id == menu.restaurant_id).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    # Verify all categories exist
    if not menu.category_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one category must be specified"
        )

    categories = db.query(MenuCategory).filter(MenuCategory.id.in_(menu.category_ids)).all()
    if len(categories) != len(menu.category_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more menu categories not found"
        )

    # Create menu without category_ids and supplement_ids (we'll set them separately)
    menu_data = menu.model_dump()
    category_ids = menu_data.pop('category_ids')

    # Handle supplements if provided
    supplements = []
    if 'supplement_ids' in menu_data and menu_data['supplement_ids']:
        supplement_ids = menu_data.pop('supplement_ids')
        supplements = db.query(Supplement).filter(Supplement.id.in_(supplement_ids)).all()
        if len(supplements) != len(supplement_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more supplements not found"
            )
    else:
        menu_data.pop('supplement_ids', None)

    db_menu = Menu(**menu_data)

    # Associate menu with categories and supplements
    db_menu.categories = categories
    if supplements:
        db_menu.supplements = supplements

    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu


@router.get("/menus", response_model=List[MenuSchema])
def list_menus(
        restaurant_id: int | None = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100),
        db: Session = Depends(get_db)
):
    query = db.query(Menu)

    if restaurant_id:
        query = query.filter(Menu.restaurant_id == restaurant_id)

    menus = query.offset(skip).limit(limit).all()

    # Calculate average ratings for all menus
    menu_ids = [menu.id for menu in menus]
    ratings = calculate_average_ratings(db, menu_ids)

    # Populate average_rating field
    for menu in menus:
        menu.average_rating = ratings.get(menu.id)

    return menus


@router.get("/menus/quick-service", response_model=List[MenuSchema])
def get_quick_service_menus(
        max_preparation_time: int = Query(30, ge=MINIMUM_PREP_TIME),
        restaurant_id: int | None = Query(None),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100),
        db: Session = Depends(get_db)
):
    query = db.query(Menu).filter(Menu.preparation_time <= max_preparation_time)

    if restaurant_id:
        query = query.filter(Menu.restaurant_id == restaurant_id)

    menus = query.offset(skip).limit(limit).all()

    # Calculate average ratings for all menus
    menu_ids = [menu.id for menu in menus]
    ratings = calculate_average_ratings(db, menu_ids)

    # Populate average_rating field
    for menu in menus:
        menu.average_rating = ratings.get(menu.id)

    return menus


@router.get("/menus/{menu_id}", response_model=MenuSchema)
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if menu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    # Calculate average rating for this menu
    ratings = calculate_average_ratings(db, [menu_id])
    menu.average_rating = ratings.get(menu_id)

    return menu


@router.put("/menus/{menu_id}", response_model=MenuSchema)
def update_menu(
        menu_id: int,
        menu_update: MenuUpdate,
        db: Session = Depends(get_db)
):
    db_menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if db_menu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    # Check preparation time if provided
    if menu_update.preparation_time is not None and menu_update.preparation_time < MINIMUM_PREP_TIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preparation time must be at least {MINIMUM_PREP_TIME} minute"
        )

    # Get update data excluding unset fields
    update_data = menu_update.model_dump(exclude_unset=True)

    # Handle category_ids separately if provided
    if "category_ids" in update_data:
        category_ids = update_data.pop("category_ids")

        # Verify all categories exist
        if not category_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one category must be specified"
            )

        categories = db.query(MenuCategory).filter(MenuCategory.id.in_(category_ids)).all()
        if len(categories) != len(category_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more menu categories not found"
            )

        # Update menu's categories
        db_menu.categories = categories

    # Handle supplement_ids separately if provided
    if "supplement_ids" in update_data:
        supplement_ids = update_data.pop("supplement_ids")

        if supplement_ids:
            supplements = db.query(Supplement).filter(Supplement.id.in_(supplement_ids)).all()
            if len(supplements) != len(supplement_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more supplements not found"
                )

            # Update menu's supplements
            db_menu.supplements = supplements
        else:
            # Clear supplements if empty list provided
            db_menu.supplements = []

    # Update other fields
    for key, value in update_data.items():
        setattr(db_menu, key, value)

    db.commit()
    db.refresh(db_menu)

    # Calculate average rating for this menu
    ratings = calculate_average_ratings(db, [db_menu.id])
    db_menu.average_rating = ratings.get(db_menu.id)

    return db_menu


@router.delete("/menus/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    db_menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if db_menu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    db.delete(db_menu)
    db.commit()
    return None


@router.get("/restaurants/{restaurant_id}/menus", response_model=List[MenuSchema])
def get_restaurant_menus(
        restaurant_id: int,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100),
        db: Session = Depends(get_db)
):
    try:
        # Verify restaurant exists
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )

        menus = db.query(Menu).filter(Menu.restaurant_id == restaurant_id).offset(skip).limit(limit).all()

        # Calculate average ratings for all menus
        menu_ids = [menu.id for menu in menus]
        ratings = calculate_average_ratings(db, menu_ids)

        # Populate average_rating field
        for menu in menus:
            menu.average_rating = ratings.get(menu.id)

        return menus
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/menus/most-rated", response_model=List[MenuSchema])
def get_most_rated_menus(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=100),
        db: Session = Depends(get_db)
):
    """Get menus ordered by their average rating (highest first)"""
    # Subquery to calculate average rating for each menu
    subquery = (
        db.query(
            Menu.id.label("menu_id"),
            func.avg(Comment.rating).label("avg_rating"),
            func.count(Comment.id).label("review_count")
        )
        .join(Comment, Menu.id == Comment.menu_id)
        .group_by(Menu.id)
        .subquery()
    )

    # Main query to get menus with their average rating
    query = (
        db.query(Menu, subquery.c.avg_rating)
        .join(
            subquery,
            Menu.id == subquery.c.menu_id
        )
        .order_by(subquery.c.avg_rating.desc(), subquery.c.review_count.desc())
    )

    results = query.offset(skip).limit(limit).all()

    # Extract menus and set average_rating
    menus = []
    for menu, avg_rating in results:
        menu.average_rating = float(avg_rating) if avg_rating is not None else None
        menus.append(menu)

    return menus
