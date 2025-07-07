from neo4j import AsyncSession
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from schemas.schema import (
 OrderItemInDB, OrderCreate, OrderInDB, OrderStatus, OrderItemCreateRequest
)

from router.user import get_user
from router.product import get_product

async def create_order(session: AsyncSession, order_data: OrderCreate) -> Optional[OrderInDB]:
    order_id = str(uuid4())
    order_date = datetime.now()
    status = OrderStatus.PENDING

    user = await get_user(session, order_data.user_id)
    if not user:
        raise ValueError(f"User with ID '{order_data.user_id}' not found.")

    username_for_order = user.name # Using user's name from UserInDB as username

    total_amount = 0.0
    products_in_order = []

    for item_req in order_data.items:
        product = await get_product(session, item_req.product_id)
        if not product:
            raise ValueError(f"Product with ID '{item_req.product_id}' not found.")

        item_price_at_order = product.price
        total_amount += item_price_at_order * item_req.quantity

        products_in_order.append({
            "id": product.product_id,
            "name": product.name,
            "quantity": item_req.quantity,
            "price_at_order": item_price_at_order
        })

    query = """
    MATCH (u:User {user_id: $user_id})
    CREATE (o:Order {
        order_id: $order_id,
        order_date: datetime($order_date),
        status: $status,
        total_amount: $total_amount
    })
    CREATE (u)-[:PLACES]->(o)
    WITH o, $products_in_order AS products_data
    UNWIND products_data AS item_data
    MATCH (p:Product {product_id: item_data.id})
    CREATE (o)-[r:CONTAINS {
        quantity: item_data.quantity,
        price_at_order: item_data.price_at_order
    }]->(p)
    RETURN o.order_id AS order_id,
           u.user_id AS user_id,
           u.name AS username,
           o.order_date AS order_date,
           o.status AS status,
           o.total_amount AS total_amount,
           COLLECT({
               product_id: p.product_id,
               product_name: p.name,
               product_price_at_order: r.price_at_order,
               quantity: r.quantity
           }) AS items
    """
    result = await session.run(query,
                               order_id=order_id,
                               user_id=order_data.user_id,
                               order_date=order_date,
                               status=status.value,
                               total_amount=total_amount,
                               products_in_order=products_in_order)
    record = await result.single()

    if record:
        return OrderInDB(
            order_id=record["order_id"],
            user_id=record["user_id"],
            username=record["username"],
            order_date=record["order_date"],
            status=OrderStatus(record["status"]),
            total_amount=record["total_amount"],
            items=[OrderItemInDB(**item) for item in record["items"]]
        )
    return None

async def get_order_details(session: AsyncSession, order_id: str) -> Optional[OrderInDB]:
    query = """
    MATCH (u:User)-[:PLACES]->(o:Order {order_id: $order_id})-[r:CONTAINS]->(p:Product)
    RETURN o.order_id AS order_id,
           u.user_id AS user_id,
           u.name AS username,
           o.order_date AS order_date,
           o.status AS status,
           o.total_amount AS total_amount,
           COLLECT({
               product_id: p.product_id,
               product_name: p.name,
               product_price_at_order: r.price_at_order,
               quantity: r.quantity
           }) AS items
    """
    result = await session.run(query, order_id=order_id)
    record = await result.single()

    if record:
        return OrderInDB(
            order_id=record["order_id"],
            user_id=record["user_id"],
            username=record["username"],
            order_date=record["order_date"],
            status=OrderStatus(record["status"]),
            total_amount=record["total_amount"],
            items=[OrderItemInDB(**item) for item in record["items"]]
        )
    return None

async def get_orders_by_user(session: AsyncSession, user_id: str) -> List[OrderInDB]:
    query = """
    MATCH (u:User {user_id: $user_id})-[:PLACES]->(o:Order)-[r:CONTAINS]->(p:Product)
    RETURN o.order_id AS order_id,
           u.user_id AS user_id,
           u.name AS username,
           o.order_date AS order_date,
           o.status AS status,
           o.total_amount AS total_amount,
           COLLECT({
               product_id: p.product_id,
               product_name: p.name,
               product_price_at_order: r.price_at_order,
               quantity: r.quantity
           }) AS items
    ORDER BY o.order_date DESC
    """
    result = await session.run(query, user_id=user_id)
    orders = []
    grouped_orders: Dict[str, Dict[str, Any]] = {}

    async for record in result:
        order_id = record["order_id"]
        if order_id not in grouped_orders:
            grouped_orders[order_id] = {
                "order_id": order_id,
                "user_id": record["user_id"],
                "username": record["username"],
                "order_date": record["order_date"],
                "status": OrderStatus(record["status"]),
                "total_amount": record["total_amount"],
                "items": []
            }
        for item in record["items"]:
            grouped_orders[order_id]["items"].append(OrderItemInDB(**item))

    for order_data in grouped_orders.values():
        orders.append(OrderInDB(**order_data))

    return sorted(orders, key=lambda o: o.order_date, reverse=True)

async def update_order_status(session: AsyncSession, order_id: str, new_status: OrderStatus) -> Optional[OrderInDB]:
    query = """
    MATCH (o:Order {order_id: $order_id})
    SET o.status = $new_status_value
    WITH o
    MATCH (o)-[r:CONTAINS]->(p:Product)
    MATCH (u:User)-[:PLACES]->(o)
    RETURN o.order_id AS order_id,
           u.user_id AS user_id,
           u.name AS username,
           o.order_date AS order_date,
           o.status AS status,
           o.total_amount AS total_amount,
           COLLECT({
               product_id: p.product_id,
               product_name: p.name,
               product_price_at_order: r.price_at_order,
               quantity: r.quantity
           }) AS items
    """
    result = await session.run(query, order_id=order_id, new_status_value=new_status.value)
    record = await result.single()

    if record:
        return OrderInDB(
            order_id=record["order_id"],
            user_id=record["user_id"],
            username=record["username"],
            order_date=record["order_date"],
            status=OrderStatus(record["status"]),
            total_amount=record["total_amount"],
            items=[OrderItemInDB(**item) for item in record["items"]]
        )
    return None