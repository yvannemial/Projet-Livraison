from datetime import datetime

from pydantic import BaseModel


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    email: str
    password: str


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    address: str | None = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderItemSupplementBase(BaseModel):
    supplement_id: int
    quantity: int


class OrderItemSupplementCreate(OrderItemSupplementBase):
    pass


class OrderItemSupplement(OrderItemSupplementBase):
    id: int
    order_item_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    menu_id: int
    quantity: int
    supplements: list[OrderItemSupplementCreate] = []


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime
    updated_at: datetime
    supplements: list[OrderItemSupplement] = []

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    client_id: int


class OrderCreate(OrderBase):
    items: list[OrderItemCreate]


class Order(OrderBase):
    id: int
    items: list[OrderItem]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RestaurantBase(BaseModel):
    name: str
    address: str
    phone_number: str
    description: str | None = None
    logo_url: str | None = None
    banner_url: str | None = None
    latitude: float
    longitude: float


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(RestaurantBase):
    name: str | None = None
    address: str | None = None
    phone_number: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    pass


class Restaurant(RestaurantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuCategoryBase(BaseModel):
    name: str
    image_url: str | None = None


class MenuCategoryCreate(MenuCategoryBase):
    pass


class MenuCategoryUpdate(BaseModel):
    name: str | None = None
    image_url: str | None = None


class MenuCategory(MenuCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplementBase(BaseModel):
    name: str
    price: float
    description: str
    preparation_time: int = 0
    image_url: str | None = None


class SupplementCreate(SupplementBase):
    pass


class SupplementUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    description: str | None = None
    preparation_time: int | None = None
    image_url: str | None = None


class Supplement(SupplementBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuBase(BaseModel):
    restaurant_id: int
    name: str
    price: float
    description: str
    preparation_time: int
    image_url: str | None = None


class MenuCreate(MenuBase):
    category_ids: list[int]
    supplement_ids: list[int] | None = None


class MenuUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    description: str | None = None
    preparation_time: int | None = None
    category_ids: list[int] | None = None
    supplement_ids: list[int] | None = None
    image_url: str | None = None


class Menu(MenuBase):
    id: int
    created_at: datetime
    updated_at: datetime
    restaurant: Restaurant | None = None
    categories: list[MenuCategory] = []
    supplements: list[Supplement] = []
    average_rating: float | None = None

    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    comment: str
    rating: int


class CommentCreate(CommentBase):
    menu_id: int
    client_id: int
    pass


class CommentUpdate(BaseModel):
    comment: str | None = None
    rating: int | None = None


class Comment(CommentBase):
    id: int
    menu_id: int
    client_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
