from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from neo4j import Session
from schemas.schema import UserBase


router = APIRouter()

# create user
@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserBase, db: Session = Depends(get_db)):

    check_query = """
    MATCH (u:User)
    WHERE u.name = $name OR u.phone = $phone
    RETURN u
    """
    existing_user = db.run(check_query, name=user.name, phone=user.phone).single()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with the name '{user.name}' or phone '{user.phone}' already exists."
        )

    create_user_query = """
    CREATE (u:User {
        user_id: $user_id,
        name: $name,
        phone: $phone,
        contact: $contact
    })
    RETURN u
    """
    params = {
        "user_id": str(uuid.uuid4()),
        "name": user.name,
        "phone": user.phone,
        "contact": user.contact
    }

    try:
        result = db.run(create_user_query, params)
        created_user_record = result.single()

        return created_user_record.data()['u']

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}" 
        )


# delete user
@router.delete("/usersDelete", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    
    find_query = "MATCH (u:User {user_id: $user_id}) RETURN u"
    find_result = db.run(find_query, user_id=user_id)
    user_node = find_result.single()

    if user_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found."
        )

    delete_query = """
    MATCH (u:User {user_id: $user_id})
    DETACH DELETE u
    """
    try:
        db.run(delete_query, user_id=user_id)
        return {"detail": "User deleted successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while deleting the user: {e}"
        )


# get user 
@router.get("/get_users", status_code=status.HTTP_200_OK)
def get_users(db: Session = Depends(get_db)):
    query = """
    MATCH (u:User)
    RETURN u
    """
    try:
        result = db.run(query)
        users = [record.data()['u'] for record in result]
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No users found."
            )
        
        return users
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )

