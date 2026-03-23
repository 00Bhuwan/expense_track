from fastapi import FastAPI
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router.router)
