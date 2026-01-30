from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional
import config

Base = declarative_base()
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String(500))
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    telegram_id = Column(Integer, nullable=False)
    items = Column(JSON, nullable=False)  # список товаров с деталями
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")  # pending, confirmed, preparing, ready, completed, cancelled
    order_type = Column(String(20), default="takeaway")  # takeaway, dine_in
    delivery_time = Column(DateTime, nullable=True)  # для заказа ко времени
    pickup_time = Column(DateTime, nullable=True)
    address = Column(String(500), nullable=True)
    notes = Column(Text)
    payment_method = Column(String(50), default="cash")  # cash, card, online
    payment_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    items = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# CRUD операции
class DatabaseManager:
    @staticmethod
    def get_or_create_user(db: Session, telegram_id: int, username: str = None,
                           first_name: str = None, last_name: str = None):
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                preferences={}
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def update_user_profile(db: Session, telegram_id: int, **kwargs):
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_user_orders(db: Session, telegram_id: int, limit: int = 10):
        return db.query(Order).filter(
            Order.telegram_id == telegram_id
        ).order_by(Order.created_at.desc()).limit(limit).all()

    @staticmethod
    def create_order(db: Session, telegram_id: int, items: list, total_amount: float,
                     order_type: str, delivery_time: datetime = None, address: str = None,
                     notes: str = None, payment_method: str = "cash"):
        import random
        import string

        # Генерация номера заказа
        order_number = f"ORD{''.join(random.choices(string.digits, k=6))}"

        order = Order(
            order_number=order_number,
            telegram_id=telegram_id,
            user_id=telegram_id,  # для простоты используем telegram_id как user_id
            items=items,
            total_amount=total_amount,
            order_type=order_type,
            delivery_time=delivery_time,
            address=address,
            notes=notes,
            payment_method=payment_method
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        # Очищаем корзину после оформления заказа
        cart = db.query(Cart).filter(Cart.telegram_id == telegram_id).first()
        if cart:
            db.delete(cart)
            db.commit()

        return order

    @staticmethod
    def update_order_status(db: Session, order_id: int, status: str):
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            order.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def get_cart(db: Session, telegram_id: int):
        cart = db.query(Cart).filter(Cart.telegram_id == telegram_id).first()
        if not cart:
            cart = Cart(telegram_id=telegram_id, items=[])
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart

    @staticmethod
    def update_cart(db: Session, telegram_id: int, items: list):
        cart = DatabaseManager.get_cart(db, telegram_id)
        cart.items = items
        cart.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cart)
        return cart


init_db()