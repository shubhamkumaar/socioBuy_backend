from pydantic import BaseModel, EmailStr
from typing import List,Optional
from datetime import datetime

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
    token: Optional[str] = None 
    name: str
    email: EmailStr
    phone: str
    

class Config:
    from_attributes = True

class ContactsUploadRequest(BaseModel):
    contacts: List[int]


class OrderItemRequest(BaseModel):
    product_name: str
    product_id: str
    quantity: int = 1

class OrderResponse(BaseModel):
    order_id: str
    user_id: str
    products: List[OrderItemRequest]
    total_price: float
    timestamp: int

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItemRequest]

class OrderCreateResponse(BaseModel):
    success: bool
    message: str
    order_id: Optional[str] = None

class OrderInDB(BaseModel):
    order_id: str
    user_id: str
    username: str
    order_date: datetime 
    status: OrderCreateResponse
    total_amount: float
    items: List[OrderResponse]