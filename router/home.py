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
    ORDER BY category // Important for deterministic LIMIT 5
    LIMIT 5 // Select up to 5 categories to process further
    
    CALL {
        WITH category
        MATCH (p:Product)
        WHERE p.productCategory = category
        WITH category, COLLECT(p) AS allProducts
        WHERE size(allProducts) > 0 // Ensure the category has at least 1 product
        RETURN category AS filteredCategory, allProducts[0..14] AS products // Slice to max 15
    }
    WITH filteredCategory, products
    WHERE filteredCategory IS NOT NULL
    ORDER BY filteredCategory
    
    UNWIND products AS product
    RETURN filteredCategory AS category, properties(product) AS product, ID(product) AS product_id
    ORDER BY category, product.name
    """

    query_default_cover = """
    MATCH (p:Product) RETURN p LIMIT 5;
    """

    query_home = """
    CALL {
        // Friends
        MATCH (u:User {phone: $phone})-[:FRIEND]->(f:User)
        RETURN f as person
        UNION
        MATCH (u:User {phone: $phone})-[:FRIEND]->(:User)-[:FRIEND]->(fof:User)
        RETURN fof as person
    }
    WITH COLLECT(person) AS person_list
    WHERE size(person_list) > 0
    
    UNWIND person_list AS person
    MATCH (person)-[:ORDERS]->(orderedProduct:Product)
    WITH DISTINCT orderedProduct.productCategory AS dynamicProductCategory
    ORDER BY dynamicProductCategory DESC
    LIMIT 5
    WITH COLLECT(dynamicProductCategory) AS productCategoriesForSearch
    WHERE size(productCategoriesForSearch) > 0
    
    UNWIND productCategoriesForSearch AS productCategory
    MATCH (pr:Product {productCategory: productCategory})
    WITH productCategory, COLLECT(pr) AS products_in_category
    RETURN productCategory, products_in_category[0..15] AS limitedProducts
    """

    query_cover = """
    CALL {
        // Friends
        MATCH (u:User {phone: $phone})-[:FRIEND]->(f:User)
        RETURN f as person
        UNION
        MATCH (u:User {phone: $phone})-[:FRIEND]->(:User)-[:FRIEND]->(fof:User)
        RETURN fof as person
    }
    WITH COLLECT(person) AS person_list
    WHERE size(person_list) > 0
    
    UNWIND person_list AS person
    MATCH (person)-[:ORDERS]->(pr:Product)
    WITH DISTINCT pr.productId AS productId, pr AS product
    ORDER BY productId DESC
    LIMIT 5
    RETURN product
    """

    categories = {}
    cover_products_list = []
    try:
        res = db.run(query_home, phone=user.phone).data()
        # if not res:
        if res:
            for item in res:
                category = item['productCategory']
                products = item['limitedProducts']
                
                if category not in categories:
                    categories[category] = []
                
                for product in products:
                    categories[category].append(product)
            cover_products = db.run(query_cover, phone=user.phone).data()
            if cover_products:
                for cover_product in cover_products:
                    cover_products_list.append(cover_product['product'])
            return {
                "categories": categories,
                "cover_products": cover_products_list
            }        
        else :
            res = db.run(query, phone=user.phone).data()
            if res:
                for item in res:
                    category = item['category']
                    product_data = item['product']
                    
                    if category not in categories:
                        categories[category] = []
                    
                    categories[category].append(product_data)
            cover_products = db.run(query_default_cover).data()
            cover_products_list = [cover_product['p'] for cover_product in cover_products]
            return {
                "categories": categories,
                "cover_products": cover_products_list
            }
    except Exception as e:
        print(f"Error fetching data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    