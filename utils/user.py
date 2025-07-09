from database import get_db
from neo4j import Session
from fastapi import Depends,HTTPException, status
from typing import List
from typing import Annotated
from router.login import verify_jwt_token
from schemas.schema import User
from schemas.schema import OrderRequest, OrderRelationDetail, MessageResponse
from datetime import datetime
from pydantic import BaseModel

class MessageResponse(BaseModel):
    user_id: str
    product_id: str
    timestamp: str


user_dependency = Annotated[User, Depends(verify_jwt_token)]

def create_friend(contact:List[str],user:user_dependency, db:Session = Depends(get_db)):
    query = """
    WITH $friendPhoneNumbers AS friendPhoneNumbers
    MATCH (u1:User {phone:$phone})
    UNWIND friendPhoneNumbers AS targetPhoneNumber
    MATCH (u2:User {phone:targetPhoneNumber})
    MERGE (u1)-[:FRIEND]->(u2)
    RETURN u1, u2
    """
    
    params = {
        "phone": user.phone,
        "friendPhoneNumbers": contact
    }
    
    try:
        result = db.run(query, params)
        created_friendship = result.single()
        return created_friendship.data()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while creating friendship: {e}"
        )
    
def create_order_relation(order_data: OrderRequest,user:user_dependency, db: Session = Depends(get_db)):

    timestamp = datetime.now().isoformat()

    query = """
    MERGE (u:User {user_id: $user_id})
    MERGE (p:Product {product_id: $product_id})
    CREATE (u)-[o:ORDERS {timestamp: $timestamp}]->(p)
    RETURN u.user_id AS user_id, p.product_id AS product_id, o.timestamp AS timestamp
    """
    
    params = {
        "user_id": user.user_id,
        "product_id": order_data.product_id,
        "timestamp": timestamp
    }

    try:
        result = db.run(query, params)
        
        created_order_record = result.single()
            
        if created_order_record: 
            return MessageResponse(
                message="Order relationship created successfully",
                detail=OrderRelationDetail(
                    user_id=created_order_record["user_id"],
                    product_id=created_order_record["product_id"],
                    timestamp=created_order_record["timestamp"]
                )
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order relationship: No result returned from database operation."
            )
    except Exception as e:
        print(f"Error creating order relationship: {e}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating order relationship: {e}"
        )