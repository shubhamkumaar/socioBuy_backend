from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from neo4j import Session,AsyncSession
from schemas.schema import UserBase
from schemas.schema import User,Product
from typing import Annotated,List, Optional
from .login import verify_jwt_token
from uuid import uuid4 
router = APIRouter(tags=["Product Management"], prefix="/products")

user_dependency = Annotated[User, Depends(verify_jwt_token)]

# create product

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED, summary="Create a new product")
async def create_product_endpoint(product: Product, db: AsyncSession = Depends(get_db)):
    check_query = """
    MATCH (p:Product)
    WHERE p.name = $name
    RETURN p
    """
    check_result = await db.run(check_query, name=product.name)
    existing_product = await check_result.single()

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A product with the name '{product.name}' already exists."
        )

    product_id = str(uuid4()) 

    create_product_query = """
    CREATE (p:Product {
        product_id: $product_id,
        name: $name,
        description: $description,
        price: $price,
        category_id: $category_id
    })
    RETURN p.product_id AS product_id, p.name AS name, p.description AS description, p.price AS price, p.category_id AS category_id
    """
    params = {
        "product_id": product_id, 
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "category_id": product.category_id
    }

    try:
        result = await db.run(create_product_query, params)
        created_product_record = await result.single()

        if created_product_record:
            return Product(
                product_id=created_product_record["product_id"],
                name=created_product_record["name"],
                description=created_product_record["description"],
                price=created_product_record["price"],
                category_id=created_product_record["category_id"]
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product record in the database."
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )


@router.get("/", response_model=List[Product], status_code=status.HTTP_200_OK, summary="Get all products")
async def get_all_products_endpoint(db: AsyncSession = Depends(get_db)): 
    query = """
    MATCH (p:Product)
    RETURN p.product_id AS product_id, p.name AS name, p.description AS description, p.price AS price, p.category_id AS category_id
    """

    try:
        result = await db.run(query)
        products = []
        async for record in result:
            products.append(Product(
                product_id=record["product_id"],
                name=record["name"],
                description=record["description"],
                price=record["price"],
                category_id=record["category_id"]
            ))

        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No products found."
            )

        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )

@router.get("/{product_id}", status_code=status.HTTP_200_OK)
def get_product(product_id: str, user:user_dependency, db: Session = Depends(get_db)):
    query = """
    MATCH (p:Product {product_id: $product_id})
    RETURN p
    """
    
    user_friend_query = f"""
    MATCH (u:User {{phone:"{user.phone}"}}) -[:FRIEND] -> (f:User) 
    RETURN f AS person
    UNION
    MATCH (u:User {{phone:"{user.phone}"}}) -[:FRIEND] -> (f:User) -[:FRIEND] ->(fof:User) 
    RETURN fof AS person
    """

    try:

        result = db.run(query, product_id=product_id)
        product_record = result.single()

        if not product_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found."
            )
        
        return product_record.data()['p']  
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )
    
    