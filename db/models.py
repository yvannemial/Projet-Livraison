from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, Enum, DateTime, Table
from sqlalchemy.orm import relationship

from db import Base

# Association table for many-to-many relationship between Menu and MenuCategory
menu_categories_association = Table(
    'menu_categories_association',
    Base.metadata,
    Column('menu_id', Integer, ForeignKey('menus.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('menu_categories.id'), primary_key=True)
)

# Association table for many-to-many relationship between Menu and Supplement
menu_supplements_association = Table(
    'menu_supplements_association',
    Base.metadata,
    Column('menu_id', Integer, ForeignKey('menus.id'), primary_key=True),
    Column('supplement_id', Integer, ForeignKey('supplements.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    password_hash = Column(String(128), nullable=False)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    orders = relationship('Order', back_populates='user')


class Restaurant(Base):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(255), nullable=True)
    banner_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    menus = relationship('Menu', back_populates='restaurant')
    orders = relationship('Order', back_populates='restaurant')


class MenuCategory(Base):
    __tablename__ ='menu_categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    menus = relationship('Menu', secondary=menu_categories_association, back_populates='categories')


class Supplement(Base):
    __tablename__ = 'supplements'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    preparation_time = Column(Integer, nullable=False, default=0)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    menus = relationship('Menu', secondary=menu_supplements_association, back_populates='supplements')


class Menu(Base):
    __tablename__ = 'menus'
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    preparation_time = Column(Integer, nullable=False, default=15)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    restaurant = relationship('Restaurant', back_populates='menus')
    categories = relationship('MenuCategory', secondary=menu_categories_association, back_populates='menus')
    supplements = relationship('Supplement', secondary=menu_supplements_association, back_populates='menus')
    comments = relationship('Comment', back_populates='menu')


class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    menu_id = Column(Integer, ForeignKey('menus.id'), nullable=False)
    comment = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    menu = relationship('Menu', back_populates='comments')


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    user = relationship('User', back_populates='orders')
    restaurant = relationship('Restaurant', back_populates='orders')
    items = relationship('OrderItem', back_populates='order')


class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    menu_id = Column(Integer, ForeignKey('menus.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    order = relationship('Order', back_populates='items')
    supplements = relationship('OrderItemSupplement', back_populates='order_item')


class Shipper(Base):
    __tablename__ = 'shippers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class OrderItemSupplement(Base):
    __tablename__ = 'order_item_supplements'
    id = Column(Integer, primary_key=True)
    order_item_id = Column(Integer, ForeignKey('order_items.id'), nullable=False)
    supplement_id = Column(Integer, ForeignKey('supplements.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    order_item = relationship('OrderItem', back_populates='supplements')
    supplement = relationship('Supplement')


class Shipment(Base):
    __tablename__ = 'shipments'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    shipper_id = Column(Integer, ForeignKey('shippers.id'), nullable=False)
    delivery_latitude = Column(Float, nullable=False)
    delivery_longitude = Column(Float, nullable=False)
    delivery_address = Column(String(255), nullable=False)
    status = Column(Enum('pending', 'completed', 'canceled'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
