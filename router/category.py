from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from neo4j import Session
from schemas.schema import UserBase
import uuid

router = APIRouter()

# create category
@router.post("/create_categories", status_code=status.HTTP_201_CREATED)
def create_category(category: UserBase, db: Session = Depends(get_db)):
    check_query = """
    MATCH (c:Category)
    WHERE c.name = $name
    RETURN c
    """
    existing_category = db.run(check_query, name=category.name).single()

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category with the name '{category.name}' already exists."
        )

    create_category_query = """
    CREATE (c:Category {
        category_id: $category_id,
        name: $name,
        products_id: []
    })
    RETURN c
    """
    params = {
        "category_id": str(uuid.uuid4()), # Generate a unique ID by self
        "name": category.name,
        "products_id": category.contact  
    }
    try:
        result = db.run(create_category_query, params)
        created_category_record = result.single()

        return created_category_record.data()['c']
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}" 
        )


# get all categories
@router.get("/get_categories", status_code=status.HTTP_200_OK)
def get_categories(db: Session = Depends(get_db)):
    query = """
    MATCH (c:Category)
    RETURN c
    """
    try:
        result = db.run(query)
        categories = [record.data()['c'] for record in result]
        return categories
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}" 
        )
    

# delete category
@router.delete("/delete_category", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, db: Session = Depends(get_db)):

    find_query = "MATCH (c:Category {category_id: $category_id}) RETURN c"


    find_result = db.run(find_query, category_id=category_id)
    category_node = find_result.single()

    if category_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID '{category_id}' not found."
        )
    
    delete_query = """
    MATCH (c:Category {category_id: $category_id})
    DETACH DELETE c
    """

    try:
        db.run(delete_query, category_id=category_id)
        return {"detail": "Category deleted successfully."}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while deleting the category: {e}"
        )
    

#add product to category
@router.put("/categories/{category_id}/add_products", status_code=status.HTTP_200_OK)
def add_products_to_category(category_id: str,AddProducts: UserBase,db: Session = Depends(get_db)):

    product_ids = AddProducts.product_ids

    if not product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID list cannot be empty."
        )

    find_category_query = "MATCH (c:Category {category_id: $category_id}) RETURN c"
    category_node = db.run(find_category_query, category_id=category_id).single()
    if category_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID '{category_id}' not found."
        )


    find_products_query = """
    MATCH (p:Product)
    WHERE p.product_id IN $product_ids
    RETURN p.product_id AS id
    """

    result = db.run(find_products_query, product_ids=product_ids)
    found_ids = {record["id"] for record in result}

    if len(found_ids) != len(set(product_ids)):
        missing_ids = list(set(product_ids) - found_ids)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The following products were not found: {missing_ids}"
        )

    add_products_query = """
    MATCH (c:Category {category_id: $category_id})
    MATCH (p:Product)
    WHERE p.product_id IN $product_ids
    MERGE (c)-[r:CONTAINS]->(p)
    RETURN c, collect(p) AS products
    """
    
    params = {
        "category_id": category_id,
        "product_ids": product_ids
    }

    try:
        result = db.run(add_products_query, params).single()        
        updated_category = dict(result.data()['c'])
        added_products = [dict(node) for node in result.data()['products']]
        
        return {
            "message": f"Successfully added {len(added_products)} products to category '{category_id}'.",
            "category": updated_category,
            "added_products": added_products
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while creating relationships: {e}"
        )
    
