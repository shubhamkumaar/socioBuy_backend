from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from neo4j import Session
from schemas.schema import UserBase


router = APIRouter()



# create product
@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: UserBase, db: Session = Depends(get_db)):
    check_query = """
    MATCH (p:Product)
    WHERE p.name = $name
    RETURN p
    """
    existing_product = db.run(check_query, name=product.name).single()

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A product with the name '{product.name}' already exists."
        )

    create_product_query = """
    CREATE (p:Product {
        name: $name,
        description: $description,
        price: $price
        category_id: $category_id
    })
    RETURN p
    """
    params = {

        "name": product.name,
        "price": product.price,
        "description": product.description,
        "category_id": product.category_id
    }

    try:
        result = db.run(create_product_query, params)
        created_product_record = result.single()

        return created_product_record.data()['p']

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}" 
        )


@router.get("/get_products", status_code=status.HTTP_200_OK)
def get_products(db: Session = Depends(get_db)):
    query = """
    MATCH (p:Product)
    RETURN p
    """

    try:
        result = db.run(query)
        products = [record.data()['p'] for record in result]
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

