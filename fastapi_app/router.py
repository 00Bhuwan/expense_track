from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, get_db
from .models import User, Transaction
from typing import Optional, List
from .crud import get_users, create_user, get_transactions, create_transaction, update_transaction, delete_transaction, TransactionType

router = APIRouter()

@router.get("/")
async def users(user_id: Optional[int] = None, db: Session = Depends(get_db)):
   return get_users(db, user_id)

@router.get("/users/{user_id}")
def get_users_endpoint(user_id: int, db: Session = Depends(get_db)):
    return get_users(db, user_id)

@router.post("/users")
async def create_user_endpoint(username: str,
                      password: str,
                      email: Optional[str] = None,
                      db: Session = Depends(get_db)
                      ):
    return create_user(db, username, password, email)

@router.get("/transactions")
async def fetch_transactions_endpoint(transaction_id: Optional[int] = None, db: Session = Depends(get_db)):
    return get_transactions(db, transaction_id)

@router.get("/transactions/{transaction_id}")
def trans_id_endpoint(transaction_id: int, db: Session = Depends(get_db)):
    return get_transactions(db, transaction_id)

@router.post("/transactions")
async def create_new_transaction(user_id: int,
        title: str,
        amount: float,
        category: str,
        t_type: Optional[TransactionType] = None,
        db: Session = Depends(get_db)):
    return create_transaction(db, user_id, title, amount, category, t_type)

@router.put("/transactions")
async def update_transaction_endpoint(transaction_id: int,
                                      title:str, amount: float,
                                      t_type: Optional[TransactionType] = None,
                                      category: Optional[str] = None,
                                      db: Session = Depends(get_db)):
    t_type_value = t_type.value if t_type else None
    return update_transaction(db, transaction_id, title, amount, category, t_type_value)

@router.delete("/transactions/{transaction_id}")
async def delete_transaction_endpoint(transaction_id: int, db: Session = Depends(get_db)):
    return delete_transaction(db, transaction_id)
