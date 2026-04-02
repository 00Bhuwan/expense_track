from sqlalchemy.orm import Session
from .models import User, Transaction
from typing import List, Optional
from enum import Enum
from datetime import datetime, UTC
from fastapi import HTTPException

class TransactionType(str, Enum):
    Income = "income"
    Expense = "expense"

def get_users(db: Session, user_id: Optional[int]) -> List[User]:
    query = db.query(User)

    if user_id is not None:
        query = query.filter(User.id == user_id)

    return query.all()

def create_user(db: Session, username: str, password: str, email: str) -> User:
    existing_user = db.query(User).filter(User.username==username, User.email==email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    db_user = User(username=username, email=email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_transactions(db: Session, transaction_id: Optional[int]) -> List[Transaction]:
    db_transactions = db.query(Transaction)

    if transaction_id is not None:
        db_transactions = db_transactions.filter(Transaction.id == transaction_id)

    return db_transactions.all()

def create_transaction(
        db: Session, user_id: int, title: str, amount: float,
        category: str, t_type: Optional[TransactionType] = None
        ) -> Transaction:
    type_value = t_type.value if t_type else None

    existing = db.query(Transaction).filter(Transaction.title==title,
                                            Transaction.amount==amount,
                                            Transaction.category==category).first()
    if existing:
        raise HTTPException(status_code=400, detail="Transaction already exists")

    transaction = Transaction(
        user_id=user_id,
        title=title,
        amount=amount,
        t_type=type_value,
        category=category,
        date = datetime.now(UTC)
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def delete_transaction(db: Session, transaction_id: int) -> dict:
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"detail": "Transaction deleted"}

def update_transaction(
        db: Session, transaction_id: int,
        title:str, amount: float,
        category: str,
        t_type: Optional[str] = None
        ):

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction.title = title
    transaction.amount = amount
    transaction.t_type = t_type
    transaction.category = category
    transaction.date = datetime.now(UTC)

    db.commit()
    db.refresh(transaction)
    return transaction
