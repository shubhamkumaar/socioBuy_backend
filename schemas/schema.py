from pydantic import BaseModel
from typing import List

class UserBase(BaseModel):
    name: str
    phone: int
    contact:List[str] = []

class Order(BaseModel):
    user_id: int
    product_id: int
    quantity: int = 1
    price_at_purchase: float
    timestamp: int  

class Product(BaseModel):
    name: str
    description: str
    price: float
    category_id: str   

class Category(BaseModel):
    category_id: str
    name: str
    products_id: List[int]