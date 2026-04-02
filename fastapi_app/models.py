from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime, UTC
from .database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password = Column(String(80), nullable=False)
    join_date = Column(DateTime, nullable=False, default=datetime.now(UTC))

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    t_type = Column(String(10))
    category = Column(String(100))
    date = Column(DateTime, default=datetime.now(UTC))

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)