from pydantic import BaseModel, Field
from typing import Optional,List
import uuid

class User(BaseModel):
    user_id: uuid.UUID
    name: str
    phone: str
    contact:List[str] = []
    email: str
    password: str

class Category(BaseModel):
    category_id: str
    name: str
    products_id: List[int]

class Product(BaseModel):
    product_id: str 
    name: str
    description: Optional[str] = None
    price: float

class Order(BaseModel):
    order_id: uuid.UUID
    product_id: int
    quantity: int = 1
    price_at_purchase: float
    timestamp: int
