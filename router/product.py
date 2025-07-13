
from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from neo4j import Session,AsyncSession
from schemas.schema import User,Product
from typing import Annotated,List, Optional
from .login import verify_jwt_token
from uuid import uuid4

router = APIRouter(tags=["Product Management"], prefix="/products")

user_dependency = Annotated[User, Depends(verify_jwt_token)]


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED, summary="Create a new product")
async def create_product_endpoint(product_input: Product, db: AsyncSession = Depends(get_db)):
    check_query = """
    MATCH (p:Product)
    WHERE p.name = $name
    RETURN p
    """
    check_result = await db.run(check_query, name=product_input.name)
    existing_product = await check_result.single()

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A product with the name '{product_input.name}' already exists."
        )

    generated_product_id = str(uuid4()) # Your code generates this UUID

    create_product_query = """
    CREATE (p:Product {
        productId: $generated_product_id,
        name: $name,
        description: $description,
        price: $price,
        category_id: $category_id
    })
    RETURN p.productId AS productId, p.name AS name, p.description AS description, p.price AS price, p.category_id AS category_id
    """
    params = {
        "generated_product_id": generated_product_id,
        "name": product_input.name,
        "price": product_input.price,
        "description": product_input.description,
        "category_id": product_input.category_id
    }

    try:
        result = await db.run(create_product_query, params)
        created_product_record = await result.single()

        if created_product_record:
            return Product(
                productId=created_product_record["productId"],
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
    RETURN p.productId AS productId, p.name AS name, p.description AS description, p.price AS price, p.category_id AS category_id
    """

    try:
        result = await db.run(query)
        products = []
        async for record in result:
            products.append(Product(
                productId=record["productId"],
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
def get_product(product_id: int, user:user_dependency, db: Session = Depends(get_db)):
    """
    Get a product by its ID.
    Returns the product details if found.
    """

    product_query = """
    MATCH (target:Product {productId: $productId})
    RETURN {
      same_product: [],
      same_brand: [],
      product:target
    } AS result
    """

    mutual_friends_who_ordered_query = """
    MATCH (target:Product {productId: $productId})
    WITH target.productBrand AS targetBrand, target.productId AS targetId, target
    CALL () {
        MATCH (u:User {phone: $phone})-[:FRIEND]->(f:User)
        RETURN f AS person, 'direct' AS relation
        UNION
        MATCH (u:User {phone: $phone})-[:FRIEND]->(:User)-[:FRIEND]->(fof:User)
        RETURN fof AS person, 'fof' AS relation
    }
    WITH targetBrand, targetId, person, relation, target
    WHERE person.phone <> $phone
    
    MATCH (person)-[ts:ORDERS]->(p:Product)
    WHERE p.productId = targetId OR p.productBrand = targetBrand
    
    WITH
      target,
      CASE WHEN p.productId = targetId THEN 'same_product' ELSE 'same_brand' END AS match_type,
      {
        name: person.name,
        relation: relation,
        productName: p.productName,
        productId: p.productId,
        productBrand: p.productBrand,
        timestamp:ts.timestamp
      } AS personData
    
    // Step 5: Separate collections for each type
    WITH
      target,
      collect(CASE WHEN match_type = 'same_product' THEN personData ELSE NULL END) AS same_product_list,
      collect(CASE WHEN match_type = 'same_brand' THEN personData ELSE NULL END) AS same_brand_list
    
    // Step 6: Filter NULLs and return as a single map
    RETURN {
      same_product: [p IN same_product_list WHERE p IS NOT NULL],
      same_brand: [p IN same_brand_list WHERE p IS NOT NULL],
      product:target
    } AS result
    """
    try:
        friends = db.run(mutual_friends_who_ordered_query, phone=user.phone, productId=product_id).data()
        if not friends:
                    friends = db.run(product_query, phone=user.phone, productId=product_id).data()

        return friends[0]['result']
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )