from database import get_db
from fastapi import APIRouter, HTTPException, Depends
from neo4j import Session

def create_user_relation(user_id: str, target_user_id: str, db: Session = Depends(get_db)):
    query = """
    MATCH (u1:User {id: $user_id}), (u2:User {id: $target_user_id})
    CREATE (u1)-[r:FRIEND]->(u2)
    RETURN r
    """ % "FRIEND" 
    result = db.run(query, user_id=user_id, target_user_id=target_user_id)
    if not result.single():
        raise HTTPException(status_code=404, detail="Relation creation failed")
