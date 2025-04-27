from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, confloat
from typing import List, Dict
import requests
from datetime import datetime, timedelta

from db import get_db
from db.models import Menu, Restaurant

router = APIRouter()


# Enhanced request models with validation
class LocationCoordinates(BaseModel):
    latitude: confloat(ge=-90, le=90)
    longitude: confloat(ge=-180, le=180)
    address: str

    @field_validator('address')
    def address_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Address cannot be empty')
        return v.strip()


class PreOrderEstimateRequest(BaseModel):
    restaurant_id: int
    delivery_location: LocationCoordinates
    menu_items: Dict[int, int]  # menu_id: quantity

    @field_validator('menu_items')
    def menu_items_not_empty(cls, v):
        if not v:
            raise ValueError('Must include at least one menu item')
        if any(quantity <= 0 for quantity in v.values()):
            raise ValueError('All quantities must be positive')
        return v


class EstimateResponse(BaseModel):
    restaurant_name: str
    restaurant_address: str
    delivery_address: str
    distance_km: float
    preparation_time_minutes: int
    estimated_delivery_duration_minutes: float
    total_estimated_time_minutes: float
    estimated_delivery_time: datetime
    # menu_items_summary: List[Dict[str, any]]
    total_order_price: float


# Constants
AVERAGE_PICKUP_TIME = 5  # minutes
AVERAGE_DROPOFF_TIME = 5  # minutes
OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/bike"


def get_bike_route(
        origin: tuple[float, float],
        destination: tuple[float, float]
) -> dict:
    """Get routing information from OSRM bike service"""
    url = f"{OSRM_BASE_URL}/{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
    params = {
        "overview": "false",
        "alternatives": "false",
        "annotations": "false"
    }

    try:
        response = requests.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        if data["code"] != "Ok":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not calculate route"
            )

        return data["routes"][0]

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Routing service error: {str(exc)}"
        )


def calculate_preparation_time(menu_items_with_quantity: List[dict]) -> int:
    """
    Calculate the total preparation time considering quantities and parallel preparation
    """
    # Group items that can be prepared in parallel
    preparation_times = []

    for item in menu_items_with_quantity:
        # Add preparation time multiplied by quantity factor
        # Using diminishing returns for multiple quantities
        quantity = item['quantity']
        base_time = item['menu'].preparation_time

        if quantity == 1:
            prep_time = base_time
        else:
            # Each additional item adds 50% more time
            prep_time = base_time * (1 + (quantity - 1) * 0.5)

        preparation_times.append(prep_time)

    # Return the longest preparation time (critical path)
    return round(max(preparation_times))


@router.post("/delivery-estimate", response_model=EstimateResponse)
async def estimate_delivery_time(
        request: PreOrderEstimateRequest,
        db: Session = Depends(get_db)
):
    """
    Calculate estimated delivery time and cost before creating an order.
    Takes into account:
    - Restaurant location
    - Delivery location
    - Menu items and their quantities
    - Preparation times
    - Bicycle routing time
    """

    try:
        # Verify a restaurant exists and gets its details
        restaurant = db.query(Restaurant).filter(Restaurant.id == request.restaurant_id).first()
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )

        # Get menu items
        menu_items = []
        total_price = 0.0
        # menu_items_summary = []

        for menu_id, quantity in request.menu_items.items():
            menu_item = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Menu item with id {menu_id} not found"
                )

            if menu_item.restaurant_id != restaurant.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Menu item {menu_id} does not belong to the selected restaurant"
                )

            menu_items.append({
                "menu": menu_item,
                "quantity": quantity
            })

            item_total = menu_item.price * quantity
            total_price += item_total

            # menu_items_summary.append({
            #     "id": menu_id,
            #     "name": menu_item.name,
            #     "quantity": quantity,
            #     "unit_price": menu_item.price,
            #     "total_price": item_total,
            #     "preparation_time": menu_item.preparation_time
            # })

        # Calculate route
        restaurant_coords = (restaurant.latitude, restaurant.longitude)
        delivery_coords = (
            request.delivery_location.latitude,
            request.delivery_location.longitude
        )

        route_details = get_bike_route(restaurant_coords, delivery_coords)

        # Calculate times
        distance_km = route_details["distance"] / 1000
        cycling_duration_minutes = route_details["duration"] / 60
        preparation_time = calculate_preparation_time(menu_items)

        # Calculate total delivery time
        total_delivery_time = (
                preparation_time +  # Kitchen preparation
                AVERAGE_PICKUP_TIME +  # Restaurant pickup
                cycling_duration_minutes +  # Cycling time
                AVERAGE_DROPOFF_TIME  # Customer dropoff
        )

        # Calculate estimated delivery time
        current_time = datetime.now()
        estimated_delivery_time = current_time + timedelta(minutes=total_delivery_time)

        return EstimateResponse(
            restaurant_name=restaurant.name,
            restaurant_address=restaurant.address,
            delivery_address=request.delivery_location.address,
            distance_km=round(distance_km, 2),
            preparation_time_minutes=preparation_time,
            estimated_delivery_duration_minutes=round(cycling_duration_minutes, 2),
            total_estimated_time_minutes=round(total_delivery_time, 2),
            estimated_delivery_time=estimated_delivery_time,
            # menu_items_summary=menu_items_summary,
            total_order_price=round(total_price, 2)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

