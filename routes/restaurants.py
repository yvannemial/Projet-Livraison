from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db import get_db
from db.models import Restaurant
from db.schemas import RestaurantCreate, Restaurant as RestaurantSchema, RestaurantUpdate

router = APIRouter()


@router.post("/restaurants", response_model=RestaurantSchema, status_code=status.HTTP_201_CREATED)
def create_restaurant(restaurant: RestaurantCreate, db: Session = Depends(get_db)):
    try:
        db_restaurant = Restaurant(**restaurant.model_dump())
        db.add(db_restaurant)
        db.commit()
        db.refresh(db_restaurant)
        return db_restaurant
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/restaurants", response_model=List[RestaurantSchema])
def list_restaurants(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    restaurants = db.query(Restaurant).offset(skip).limit(limit).all()
    return restaurants


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantSchema)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    return restaurant


@router.put("/restaurants/{restaurant_id}", response_model=RestaurantSchema)
def update_restaurant(
        restaurant_id: int,
        restaurant_update: RestaurantUpdate,
        db: Session = Depends(get_db)
):
    db_restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if db_restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    # Update restaurant attributes
    for key, value in restaurant_update.model_dump().items():
        setattr(db_restaurant, key, value)

    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


@router.delete("/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    db_restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if db_restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    db.delete(db_restaurant)
    db.commit()
    return None
