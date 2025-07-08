from database import get_db
from neo4j import Session
from fastapi import Depends,HTTPException, status
from typing import List
from typing import Annotated
from router.login import verify_jwt_token
from schemas.schema import User

user_dependency = Annotated[User, Depends(verify_jwt_token)]
def create_friend(contact:List[str],user:user_dependency, db:Session = Depends(get_db)):
    query = """
    WITH $friendPhoneNumbers AS friendPhoneNumbers
    MATCH (u1:User {phone:$phone})
    UNWIND friendPhoneNumbers AS targetPhoneNumber
    MATCH (u2:User {phone:targetPhoneNumber})
    MERGE (u1)-[:FRIEND]->(u2)
    RETURN u1, u2
    """
    
    params = {
        "phone": user.phone,
        "friendPhoneNumbers": contact
    }
    
    try:
        result = db.run(query, params)
        created_friendship = result.single()
        return created_friendship.data()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while creating friendship: {e}"
        )