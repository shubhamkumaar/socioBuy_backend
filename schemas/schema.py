from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class User(BaseModel):
    id: str
    name: str
    phone: str
    email: EmailStr
    
class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class UserBase(BaseModel):
    name: str
    phone: str
    contact:List[int] = []
    email: EmailStr
    password: str

class UserInDB(BaseModel):
    user_id: str 
    name: str
    phone: str
    email: EmailStr
    contact: List[str] = [] 

class Product(BaseModel):
    productId: str
    name: str
    description: str
    price: float
    category_id: str

class Category(BaseModel):
    category_id: str
    name: str
    productId: List[int]

class AddProducts(BaseModel):
    productIds: List[int]

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

class ContactsUploadRequest(BaseModel):
    contacts: List[int]

class OrderItemCreateRequest(BaseModel):
    productId: str
    quantity: int = 1

class OrderItemInDB(BaseModel):
    productId: str
    product_name: str
    product_price_at_order: float
    quantity: int

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItemCreateRequest]

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderInDB(BaseModel):
    order_id: str
    user_id: str
    username: str 
    order_date: datetime
    status: OrderStatus
    total_amount: float
    items: List[OrderItemInDB]


class OrderRequest(BaseModel):
    productId: List[str]

class OrderRelationDetail(BaseModel):
    email: EmailStr
    productId: int
    timestamp: str

class OrderCreationResponse(BaseModel):
    message: str
    created_orders: List[OrderRelationDetail]