from neo4j import Session
from fastapi import Depends,HTTPException, status
from typing import List
from typing import Annotated
from router.login import verify_jwt_token
from schemas.schema import User
from schemas.schema import OrderRequest, OrderRelationDetail, OrderCreationResponse
from datetime import datetime
from pydantic import BaseModel

class MessageResponse(BaseModel):
    user_id: str
    product_id: str
    timestamp: str


user_dependency = Annotated[User, Depends(verify_jwt_token)]


def create_friend(contact:List[str],phone, db:Session):
    print(f"phone: form utils file {phone}")
    query = """
    MATCH (u1:User {phone:$phone})
    WITH u1, $friendPhoneNumbers AS friendPhoneNumbers
    UNWIND friendPhoneNumbers AS targetPhoneNumber
    OPTIONAL MATCH (u2:User {phone:targetPhoneNumber})
    FOREACH (
        n IN CASE WHEN u2 IS NOT NULL THEN [1] ELSE [] END | // Only execute if u2 is found
        MERGE (u1)-[:FRIEND]->(u2)
    )
    RETURN u1.phone AS user1Phone, u2.phone AS user2Phone, targetPhoneNumber, // Return specific properties
           CASE WHEN u2 IS NOT NULL THEN true ELSE false END AS u2_found,
           CASE WHEN (u1)-[:FRIEND]->(u2) THEN true ELSE false END AS friendship_exists_after_merge // Check if relation exists
    """
    
    try:
        print("Executing query...")
        # Get all results, as contact can be a list of multiple phone numbers
        all_results = db.run(query, phone=phone, friendPhoneNumbers=contact).data()
        

        if not all_results:
            # This case means u1 (the current user) was not found.
            # The initial MATCH (u1:User {phone:$phone}) failed.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with phone number {phone} not found. Cannot create friendship."
            )

        successfully_processed_friends = []
        failed_to_find_friends = []

        # Iterate through the results to see what happened for each targetPhoneNumber
        for record in all_results:
            user1_phone = record.get('user1Phone')
            user2_phone = record.get('user2Phone')
            target_phone_number_from_query = record.get('targetPhoneNumber')
            u2_found = record.get('u2_found')
            friendship_exists = record.get('friendship_exists_after_merge')

            if u2_found: # This means u2 was found, and MERGE would have run
                successfully_processed_friends.append({
                    "target_phone": target_phone_number_from_query,
                    "friendship_status": "CREATED" if friendship_exists else "ALREADY_EXISTS"
                })
            else: # u2 was not found
                failed_to_find_friends.append(target_phone_number_from_query)

        response_message = "Friendship processing complete."
        if failed_to_find_friends:
            response_message += (
                f" Could not find users with phone numbers: "
                f"{', '.join(failed_to_find_friends)}."
            )
        if not successfully_processed_friends and not failed_to_find_friends:
             # This highly unlikely if all_results is not empty, but good for robustness
             response_message = "No friends processed due to an unknown issue."

        print(f"Successfully processed friends: {successfully_processed_friends}")
        print(f"Failed to find friends: {failed_to_find_friends}")
        return {
            "message": response_message,
            "processed_friends": successfully_processed_friends,
            "failed_to_find": failed_to_find_friends
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in create_friend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while creating friendship: {e}"
        )
    
def create_order_relation(order_data: List[str], user: user_dependency, db: Session) -> OrderCreationResponse:

    timestamp = datetime.now().isoformat()

    query = """
    MERGE (u:User {email: $email})
    WITH u, $product_ids AS product_ids_list  // <--- ADDED THIS LINE: Carry 'u' and the list for UNWIND
    UNWIND product_ids_list AS single_product_id
    MERGE (p:Product {product_id: single_product_id})
    CREATE (u)-[o:ORDERS {timestamp: $timestamp}]->(p)
    RETURN u.email AS email, single_product_id AS product_id, o.timestamp AS timestamp // Changed u.user_id to u.email for consistency with OrderRelationDetail schema
    """

    params = {
        "email": user.email,
        "product_ids": order_data,
        "timestamp": timestamp
    }

    try:
        result = db.run(query, params)

        created_order_records = result.data()

        if created_order_records:
            created_orders_list = [
                OrderRelationDetail(
                    email=record["email"], # Make sure 'email' is returned by the query
                    product_id=record["product_id"],
                    timestamp=record["timestamp"]
                )
                for record in created_order_records
            ]

            return OrderCreationResponse(
                message=f"Successfully created {len(created_orders_list)} order relationship(s).",
                created_orders=created_orders_list
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order relationships: No results returned from database operation. Check if product_ids list was empty or an internal error occurred."
            )
    except Exception as e:
        print(f"Error creating order relationships: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating order relationships: {e}"
        )