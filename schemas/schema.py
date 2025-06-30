from pydantic import BaseModel
from typing import List

class User(BaseModel):
    id: int
    name: str
    phone: str
    contact:List[str] = []

class Order(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int    

class Product(BaseModel):
    id: int
    name: str
    price: float    