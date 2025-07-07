from fastapi import FastAPI, Depends
from database import get_db
from neo4j import Session
import config
from functools import lru_cache
from router.user import router as user_router 
from router.login import router as login_router
from router.order import router as order_router
from router.product import router as product_router 
app = FastAPI()

@lru_cache
def get_settings():
    return config.Settings()

Settings = get_settings()

app.include_router(user_router)

app.include_router(login_router)

app.include_router(order_router)

app.include_router(product_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/db")
def read_db(db: Session = Depends(get_db)):
    # Use the db session here
    return {"db": "connection established"}