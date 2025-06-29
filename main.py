from fastapi import FastAPI
from functools import lru_cache
from config import Settings
from database import get_db
from fastapi import APIRouter, HTTPException, Depends
from neo4j import Session

app = FastAPI()

import config
from functools import lru_cache

@lru_cache
def get_settings():
    return config.Settings()

Settings = get_settings()

@app.get("/")
def read_root():
    print(Settings)
    return {"Hello": "World"}

@app.get("/db")
def read_db(db: Session = Depends(get_db)):
    # Use the db session here
    return {"db": "connection established"}