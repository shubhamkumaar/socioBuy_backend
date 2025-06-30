from pydantic import BaseModel
from typing import List

class UserBase(BaseModel):
    name: str
    phone: int
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