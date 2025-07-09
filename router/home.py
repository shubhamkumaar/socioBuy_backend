from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from router.login import verify_jwt_token
from schemas.schema import User
from neo4j import Session
from database import get_db
import json
router = APIRouter(tags=["home"])


user_dependency = Annotated[User, Depends(verify_jwt_token)]

@router.get("/", summary="Home Page")
async def home(user:user_dependency,db:Session = Depends(get_db)):
    """
    Home page endpoint.
    Returns a welcome message.
    """
    query = """
MATCH (c:Product)
WITH DISTINCT c.product_category AS category
ORDER BY category // Important for deterministic LIMIT 6
LIMIT 6 // Select up to 6 categories to process further

CALL {
    WITH category
    MATCH (p:Product)
    WHERE p.product_category = category
    WITH category, COLLECT(p) AS allProducts
    WHERE size(allProducts) > 0 // Ensure the category has at least 1 product
    RETURN category AS filteredCategory, allProducts[0..19] AS products // Slice to max 20
}
WITH filteredCategory, products
WHERE filteredCategory IS NOT NULL
ORDER BY filteredCategory

UNWIND products AS product
RETURN filteredCategory AS category, properties(product) AS product, ID(product) AS product_id
ORDER BY category, product.name
    """

    try:
        res = db.run(query).data()
        grouped_by_category = {}
        
        for item in res:
            category = item['category']
            product_data = item['product']     
        
            if category not in grouped_by_category:
                grouped_by_category[category] = []
        
            grouped_by_category[category].append(product_data)
        
        return {"Product":grouped_by_category}
    except:
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetch"
            )

