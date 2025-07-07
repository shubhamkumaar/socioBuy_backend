from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from neo4j import AsyncSession 
from schemas.schema import Product 
from typing import List, Optional
from uuid import uuid4 

router = APIRouter(prefix="/products", tags=["Products"]) 

async def get_product(session: AsyncSession, product_id: str) -> Optional[Product]:
    query = """
    MATCH (p:Product {product_id: $product_id})
    RETURN p.product_id AS product_id, p.name AS name, p.description AS description, p.price AS price, p.category_id AS category_id
    """
    result = await session.run(query, product_id=product_id)
    record = await result.single()
    if record:
        return Product(
            product_id=record["product_id"],
            name=record["name"],
            description=record["description"],
            price=record["price"],
            category_id=record["category_id"]
        )
    return None


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

@router.get("/{product_id}", response_model=Product, status_code=status.HTTP_200_OK, summary="Get product details by ID")
async def get_product_details_endpoint(product_id: str, db: AsyncSession = Depends(get_db)):
    product_data = await get_product(db, product_id) # Use the internal helper function
    if not product_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product_data


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a product by ID")
async def delete_product_endpoint(product_id: str, db: AsyncSession = Depends(get_db)):
    product_node = await get_product(db, product_id) 

    if product_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found."
        )

    delete_query = """
    MATCH (p:Product {product_id: $product_id})
    DETACH DELETE p
    """
    try:
        await db.run(delete_query, product_id=product_id)
        return {} # 204 No Content typically returns an empty body
    except Exception as e:
        print(f"Error deleting product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while deleting the product: {e}"
        )