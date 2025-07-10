from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from router.login import verify_jwt_token
from schemas.schema import User
from neo4j import Session
from database import get_db

router = APIRouter(tags=["home"])


user_dependency = Annotated[User, Depends(verify_jwt_token)]

@router.get("/", summary="Home Page")
async def home(user:user_dependency,db:Session = Depends(get_db)):
    """
    Home page endpoint.
    Returns categories and products from the database.
    """
    query = """
    MATCH (c:Product)
    WITH DISTINCT c.productCategory AS category
    ORDER BY category // Important for deterministic LIMIT 6
    LIMIT 6 // Select up to 6 categories to process further
    
    CALL {
        WITH category
        MATCH (p:Product)
        WHERE p.productCategory = category
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


    query_home = """
    // Part 1: Dynamically get product categories ordered by friends/friends-of-friends
    CALL {
        MATCH (u:User {phone:"7763042401"}) - [:FRIEND] ->(f:User)
        RETURN f AS person
        UNION
        MATCH (u:User {phone:"7763042401"}) - [:FRIEND] ->(f:User)-[:FRIEND] ->(fof:User)
        RETURN fof AS person
    }
    MATCH (person) -[:ORDERS] ->(orderedProduct:Product)
    WITH DISTINCT orderedProduct.productCategory AS dynamicProductCategory
    ORDER BY dynamicProductCategory DESC
    LIMIT 5
    WITH COLLECT(dynamicProductCategory) AS productCategoriesForSearch // Collect these categories into a list
    
    UNWIND productCategoriesForSearch AS productCategory // Unwind the categories obtained from the first part
    MATCH (pr:Product{productCategory: productCategory})
    WITH productCategory, COLLECT(pr) AS products_in_category
    RETURN productCategory, products_in_category[0..15] AS limitedProducts"""

    query_cover = """
    CALL {
    MATCH (u:User {phone:"7763042401"}) - [:FRIEND] ->(f:User) return f as person
    UNION
    MATCH (u:User {phone:"7763042401"}) - [:FRIEND] ->(f:User)-[:FRIEND] ->(fof:User) return fof as person
    }
    
    MATCH (person) -[:ORDERS] ->(pr:Product)
    WITH DISTINCT pr.productId AS productId, pr AS product
    ORDER BY productId DESC
    LIMIT 5
    return product
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

