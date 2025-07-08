from neo4j import AsyncSession
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

from models import (
 OrderItemInDB, OrderCreate, OrderInDB, OrderStatus, 
)

from router.user import get_user
from router.product import get_product


async def create_order(session: AsyncSession, order_data: OrderCreate) -> Optional[OrderInDB]:
    order_id = str(uuid4())
    order_date = datetime.now().isoformat()
    status = OrderStatus.PENDING.value

    # Validate user existence
    user = await get_user(session, order_data.user_id)
    if not user:
        raise ValueError(f"User with ID '{order_data.user_id}' not found.")

    # Validate products and calculate total amount
    total_amount = 0.0
    products_in_order = [] # To store details for the order creation query
    items_for_response = [] # To store details for the OrderInDB response

    for item_req in order_data.items:
        product = await get_product(session, item_req.product_sku)
        if not product:
            raise ValueError(f"Product with SKU '{item_req.product_sku}' not found.")

        item_price_at_order = product.price # Capture price at time of order
        total_amount += item_price_at_order * item_req.quantity

        products_in_order.append({
            "sku": product.sku,
            "quantity": item_req.quantity,
            "price_at_order": item_price_at_order
        })
        items_for_response.append(OrderItemInDB(
            product_sku=product.sku,
            product_name=product.name,
            product_price_at_order=item_price_at_order,
            quantity=item_req.quantity
        ))

    query = f"""
    MATCH (u:User {{user_id: $user_id}})
    CREATE (o:Order {{
        order_id: $order_id,
        order_date: $order_date,
        status: $status,
        total_amount: $total_amount
    }})
    CREATE (u)-[:PLACES]->(o)
    WITH o, $products_in_order AS products_data
    UNWIND products_data AS item_data
    MATCH (p:Product {{sku: item_data.sku}})
    CREATE (o)-[:CONTAINS {{
        quantity: item_data.quantity,
        price_at_order: item_data.price_at_order
    }}]->(p)
    RETURN o.order_id AS order_id,
           u.user_id AS user_id,
           u.username AS username,
           o.order_date AS order_date,
           o.status AS status,
           o.total_amount AS total_amount,
           COLLECT({{
               product_sku: p.sku,
               product_name: p.name,
               product_price_at_order: CONTAINS_REL.price_at_order,
               quantity: CONTAINS_REL.quantity
           }}) AS items
    """
    result = await session.run(query,
                               order_id=order_id,
                               user_id=order_data.user_id,
                               order_date=order_date,
                               status=status,
                               total_amount=total_amount,
                               products_in_order=products_in_order)
    record = await result.single()

    if record:
        return OrderInDB(
            order_id=record["order_id"],
            user_id=record["user_id"],
            username=record["username"],
            order_date=datetime.fromisoformat(record["order_date"]),
            status=OrderStatus(record["status"]),
            total_amount=record["total_amount"],
            items=[OrderItemInDB(**item) for item in record["items"]]
        )
    return None


async def get_order(session: AsyncSession, order_id: str) -> Optional[OrderInDB]:
    query = """
    MATCH (u:User)-[:PLACES]->(o:Order {order_id: $order_id})-[:CONTAINS]->(p:Product)
    RETURN o.order_id AS order_id,
           u.user_id AS user_id,
           u.username AS username,
           o.order_date AS order_date,
           o.status AS status,
           o.total_amount AS total_amount,
           COLLECT({
               product_sku: p.sku,
               product_name: p.name,
               product_price_at_order: CONTAINS_REL.price_at_order,
               quantity: CONTAINS_REL.quantity
           }) AS items
    """
    result = await session.run(query, order_id=order_id)
    record = await result.single()

    if record:
        return OrderInDB(
            order_id=record["order_id"],
            user_id=record["user_id"],
            username=record["username"],
            order_date=datetime.fromisoformat(record["order_date"]),
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
           u.username AS username,
           o.order_date AS order_date,
           o.status AS status,
           o.total_amount AS total_amount,
           COLLECT({
               product_sku: p.sku,
               product_name: p.name,
               product_price_at_order: r.price_at_order,
               quantity: r.quantity
           }) AS items
    ORDER BY o.order_date DESC
    """
    result = await session.run(query, user_id=user_id)
    orders = []
    # Group items by order_id since COLLECT aggregates per (u)-[p]->(o) path
    grouped_orders: Dict[str, Dict[str, Any]] = {}

    async for record in result:
        order_id = record["order_id"]
        if order_id not in grouped_orders:
            grouped_orders[order_id] = {
                "order_id": order_id,
                "user_id": record["user_id"],
                "username": record["username"],
                "order_date": datetime.fromisoformat(record["order_date"]),
                "status": OrderStatus(record["status"]),
                "total_amount": record["total_amount"],
                "items": []
            }
        # Add items to the existing order
        for item in record["items"]: # COLLECT returns a list of maps, each map is an item
            grouped_orders[order_id]["items"].append(OrderItemInDB(**item))

    # Convert the grouped dictionary to a list of OrderInDB models
    for order_data in grouped_orders.values():
        orders.append(OrderInDB(**order_data))

    return sorted(orders, key=lambda o: o.order_date, reverse=True)


async def update_order_status(session: AsyncSession, order_id: str, new_status: OrderStatus) -> Optional[OrderInDB]:
    query = """
    MATCH (o:Order {order_id: $order_id})
    SET o.status = $new_status
    WITH o
    MATCH (o)-[r:CONTAINS]->(p:Product)
    MATCH (u:User)-[:PLACES]->(o)
    RETURN o.order_id AS order_id,
           u.user_id AS user_id,
           u.username AS username,
           o.order_date AS order_date,
           o.status AS status,
           o.total_amount AS total_amount,
           COLLECT({
               product_sku: p.sku,
               product_name: p.name,
               product_price_at_order: r.price_at_order,
               quantity: r.quantity
           }) AS items
    """
    result = await session.run(query, order_id=order_id, new_status=new_status.value)
    record = await result.single()

    if record:
        return OrderInDB(
            order_id=record["order_id"],
            user_id=record["user_id"],
            username=record["username"],
            order_date=datetime.fromisoformat(record["order_date"]),
            status=OrderStatus(record["status"]),
            total_amount=record["total_amount"],
            items=[OrderItemInDB(**item) for item in record["items"]]
        )
    return None