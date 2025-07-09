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
    productId: List[int]

@router.post("/ai", summary="Suggest Products")
def suggest_products(cart:CartItem,user: user_dependency, db: Session = Depends(get_db)):
    """
    Suggest products based on user preferences.
    Returns a list of suggested products.
    """

    get_products_query = """
    WITH $product_id AS p
    UNWIND p AS productId
    MATCH (pr:Product {productId:productId})
    RETURN pr """
    products = []
    try:
        res = db.run(get_products_query, product_id=cart.productId).data()
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
    product_ids = [product['productId'] for product in products]
    # print(product_ids)

    get_friend_who_ordered_query = """
    WITH $product_id AS p
    UNWIND p AS productId
    MATCH (u:User {phone: $phone})-[:FRIEND]->(f:User)-[r:ORDERS]->(pr:Product {productId: productId})
    RETURN f.name AS friend_name, pr.productName AS product_name, r.timestamp AS order_timestamp
    """
    friend_product = {}
    try:
        friends = db.run(get_friend_who_ordered_query, phone=user.phone, product_id=product_ids).data()
        for product in friends:
            product['product_name'] = product.get('product_name')
            product['friend_name'] = product.get('friend_name')
            product['order_timestamp'] = product.get('order_timestamp')
            if friend_product.get(product['product_name']) is None:
                friend_product[product['product_name']] = []
            friend_product[product['product_name']].append({"friend_name": product['friend_name'], "order_timestamp": product['order_timestamp']})

        # friend_product = [{"friend_name": friend['friend_name'], "product_name": friend['product_name']} for friend in friends]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    # print(friend_product)
    brands = [products['productBrand'] for products in products]
    brands = list(set(brands))
    # print(brands)

    friend_who_use_same_brand_query = """
    WITH $brands AS brands
    UNWIND brands AS productBrand
    MATCH (u:User {phone: $phone})-[:FRIEND]->(f:User)-[r:ORDERS]->(p:Product{productBrand: productBrand})
    WHERE p.productBrand IN brands
    RETURN f.name AS friend_name, p.productBrand AS product_brand, p.productName AS product_name, r.timestamp AS order_timestamp
    """
    friend_brand = {}
    try:
        friends = db.run(friend_who_use_same_brand_query, phone=user.phone, brands=brands).data()
        for f in friends:
            if friend_brand.get(f['product_brand']) is None:
                friend_brand[f['product_brand']] = []
            friend_brand[f['product_brand']].append({"product_name": f['product_name'], "friend_name": f['friend_name'], "order_timestamp": f['order_timestamp']})
        # friend_brand = [{"friend_name": friend['friend_name'], "product_brand": friend['product_brand']} for friend in friends]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    # print(friend_brand)

    categories = [products['productCategory'] for products in products]
    categories = list(set(categories))
    # print(categories)

    query_friend_category = """
    WITH $categories AS categories
    UNWIND categories AS productCategory
    MATCH (u:User {phone: $phone})-[:FRIEND]->(f:User)-[r:ORDERS]->(p:Product{productCategory: productCategory})
    WHERE p.productCategory IN categories
    RETURN f.name AS friend_name, p.productCategory AS product_category, p.productName AS product_name, r.timestamp AS order_timestamp
    """

    friend_category = {}
    try:
        friends = db.run(query_friend_category, phone=user.phone, categories=categories).data()
        for friend in friends:
            if friend_category.get(friend['product_category']) is None:
                friend_category[friend['product_category']] = []
            friend_category[friend['product_category']].append({"product_name": friend['product_name'], "friend_name": friend['friend_name'], "order_timestamp": friend['order_timestamp']})
        # friend_category = [{"friend_name": friend['friend_name'], "product_category": friend['product_category']} for friend in friends]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    print(friend_category)

    cart = []
    for product in products:
        c = {}
        productName = product.get('productName')
        c['productName'] = productName
        c['direct_product'] = friend_product.get(productName, [])
        c['same_brand'] = friend_brand.get(product['productBrand'], [])
        c['same_category'] = friend_category.get(product['productCategory'], [])
        cart.append(c)
    return {
        # "friend_product": friend_product,
        # "friend_category": friend_category
        # "friend_brand": friend_brand,
        # "products": products
        "cart": cart,
    }