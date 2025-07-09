from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from router.login import verify_jwt_token
from schemas.schema import User
from neo4j import Session
from database import get_db
from pydantic import BaseModel

router = APIRouter(tags=["Cart"])

user_dependency = Annotated[User, Depends(verify_jwt_token)]

class CartItem(BaseModel):  
    product_id: List[int]

@router.post("/ai", summary="Suggest Products")
async def suggest_products(cart:CartItem,user: user_dependency, db: Session = Depends(get_db)):
    """
    Suggest products based on user preferences.
    Returns a list of suggested products.
    """
    query = """
    MATCH (u:User {id: $user_id})-[:LIKES]->(p:Product)
    WITH p, COUNT(*) AS like_count
    ORDER BY like_count DESC
    LIMIT 10
    RETURN properties(p) AS product, ID(p) AS product_id
    """

    get_products_query = """
    WITH $product_id AS p
    UNWIND p AS productId
    MATCH (pr:Product {productId:productId})
    RETURN pr """
    products = []
    try:
        res = db.run(get_products_query, product_id=cart.product_id).data()
        products = [item['pr'] for item in res]
        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No products found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    