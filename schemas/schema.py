from pydantic import BaseModel, EmailStr
from typing import List,Optional

class User(BaseModel):
    id: str
    name: str
    phone: str
    email: EmailStr

class UserBase(BaseModel):
    name: str
    phone: str
    contact:List[int] = []
    email: EmailStr
    password: str

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


class AddProducts(BaseModel):
    product_ids: List[str]

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None 
    name: str
    email: EmailStr
    phone: str
    

class Config:
    from_attributes = True