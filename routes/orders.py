from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from sqlalchemy.orm import Session

from db import get_db
from db.schemas import OrderCreate, Order
from db.models import (
    Order as OrderModel, 
    Restaurant as RestaurantModel, 
    OrderItem as OrderItemModel, 
    Menu as MenuModel,
    Supplement as SupplementModel,
    OrderItemSupplement as OrderItemSupplementModel
)

router = APIRouter()


@router.post("/orders", response_model=Order)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Extract items from the order
    items = order.items

    if not items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    # Calculate the total amount and get restaurant_id
    total_amount = 0
    restaurant_id = None

    for item in items:
        menu_item = db.query(MenuModel).filter(MenuModel.id == item.menu_id).first()
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Menu item with id {item.menu_id} not found")

        # Calculate menu item price
        item_price = menu_item.price * item.quantity

        # Calculate supplements price
        supplements_price = 0
        for supplement_item in item.supplements:
            supplement = db.query(SupplementModel).filter(SupplementModel.id == supplement_item.supplement_id).first()
            if not supplement:
                raise HTTPException(status_code=404, detail=f"Supplement with id {supplement_item.supplement_id} not found")

            # Verify that the supplement is available for this menu
            if supplement not in menu_item.supplements:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Supplement with id {supplement_item.supplement_id} is not available for menu item with id {item.menu_id}"
                )

            supplements_price += supplement.price * supplement_item.quantity

        total_amount += item_price + supplements_price

        # Set restaurant_id from the first menu item
        if restaurant_id is None:
            restaurant_id = menu_item.restaurant_id
        # Validate that all menu items belong to the same restaurant
        elif restaurant_id != menu_item.restaurant_id:
            raise HTTPException(status_code=400, detail="All menu items must belong to the same restaurant")

    # Create order without items
    order_data = order.model_dump(exclude={"items"})
    db_order = OrderModel(**order_data, total_amount=total_amount, restaurant_id=restaurant_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # Create order items
    for item in items:
        db_order_item = OrderItemModel(
            order_id=db_order.id,
            menu_id=item.menu_id,
            quantity=item.quantity
        )
        db.add(db_order_item)
        db.flush()  # Flush to get the order_item.id

        # Create order item supplements
        for supplement_item in item.supplements:
            db_order_item_supplement = OrderItemSupplementModel(
                order_item_id=db_order_item.id,
                supplement_id=supplement_item.supplement_id,
                quantity=supplement_item.quantity
            )
            db.add(db_order_item_supplement)

    db.commit()
    db.refresh(db_order)

    return db_order


@router.get("/orders/{order_id}", response_model=Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")

    return db_order


@router.get("/users/{user_id}/orders", response_model=list[Order])
def list_user_orders(
        user_id: int,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1),
        db: Session = Depends(get_db)
):
    user = db.query(RestaurantModel).filter(RestaurantModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return db.query(OrderModel).filter(OrderModel.client_id == user_id).offset(skip).limit(limit).all()


@router.get("/restaurants/{restaurant_id}/orders", response_model=list[Order])
def list_restaurant_orders(
        restaurant_id: int,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1),
        db: Session = Depends(get_db)
):
    restaurant = db.query(RestaurantModel).filter(RestaurantModel.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return db.query(OrderModel).filter(OrderModel.restaurant_id == restaurant_id).offset(skip).limit(limit).all()
