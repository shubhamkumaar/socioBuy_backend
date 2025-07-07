from fastapi import APIRouter, HTTPException, Depends, status
from neo4j import AsyncSession
from typing import List

from database import get_db
from schemas.schema import OrderCreate, OrderInDB, OrderStatusUpdate, OrderStatus # Changed import

from utils.order import create_order, update_order_status, get_order_details

router = APIRouter(tags=["Order Management"],prefix="/orders")

@router.post("/", response_model=OrderInDB, status_code=status.HTTP_201_CREATED, summary="Place a new order")
async def create_order_endpoint(order: OrderCreate, session: AsyncSession = Depends(get_db)):
    try:
        order_in_db = await create_order(session, order)
        if not order_in_db:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create order.")
        return order_in_db
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error creating order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating the order.")

@router.put("/{order_id}/status", response_model=OrderInDB, status_code=status.HTTP_200_OK, summary="Update order status")
async def update_order_status_endpoint(order_id: str, status_update: OrderStatusUpdate, session: AsyncSession = Depends(get_db)):
    try:
        updated_order = await update_order_status(session, order_id, status_update.status)
        if not updated_order:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found for status update.")
        return updated_order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error updating order status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while updating the order status.")

@router.get("/{order_id}", response_model=OrderInDB, status_code=status.HTTP_200_OK, summary="Get order details")
async def get_order_details_endpoint(order_id: str, session: AsyncSession = Depends(get_db)):
    try:
        order_details = await get_order_details(session, order_id)
        if not order_details:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        return order_details
    except Exception as e:
        print(f"Error retrieving order details: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while retrieving the order details.")