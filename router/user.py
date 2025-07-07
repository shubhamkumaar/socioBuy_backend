from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from neo4j import AsyncSession 
from schemas.schema import UserBase, UserInDB, ContactsUploadRequest 
from typing import List, Dict, Optional
from uuid import uuid4 

router = APIRouter(prefix="/users", tags=["Users"])

async def get_user(session: AsyncSession, user_id: str) -> Optional[UserInDB]:
    query = """
    MATCH (u:User {user_id: $user_id})
    RETURN u.user_id AS user_id, u.name AS name, u.email AS email, u.phone AS phone, u.contact AS contact
    """
    result = await session.run(query, user_id=user_id)
    record = await result.single()
    if record:
        contact_list = record.get("contact", [])
        if contact_list is None: # Handle cases where contact might be null in DB
            contact_list = []
        return UserInDB(
            user_id=record["user_id"],
            name=record["name"],
            email=record["email"],
            phone=record["phone"],
            contact=contact_list
        )
    return None

@router.post("/", response_model=UserInDB, status_code=status.HTTP_201_CREATED, summary="Create a new user")
async def create_user_endpoint(user: UserBase, db: AsyncSession = Depends(get_db)): 

    check_query = """
    MATCH (u:User)
    WHERE u.email = $email OR u.phone = $phone
    RETURN u
    """
    check_result = await db.run(check_query, email=user.email, phone=user.phone)
    existing_user = await check_result.single()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with the email '{user.email}' or phone '{user.phone}' already exists."
        )

    user_id = str(uuid4()) 

    create_user_query = """
    CREATE (u:User {
        user_id: $user_id,
        name: $name,
        phone: $phone,
        contact: $contact,
        email: $email
    })
    RETURN u.user_id AS user_id, u.name AS name, u.email AS email, u.phone AS phone, u.contact AS contact
    """
    params = {
        "user_id": user_id,
        "name": user.name,
        "phone": user.phone,
        "contact": user.contact,
        "email": user.email
   
    }

    try:
        result = await db.run(create_user_query, params)
        created_user_record = await result.single()

        if created_user_record:
            return UserInDB(
                user_id=created_user_record["user_id"],
                name=created_user_record["name"],
                email=created_user_record["email"],
                phone=created_user_record["phone"],
                contact=created_user_record.get("contact", [])
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user record in the database."
        )

    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )

# delete user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user by ID")
async def delete_user_endpoint(user_id: str, db: AsyncSession = Depends(get_db)): # Use AsyncSession

    user_node = await get_user(db, user_id) # Use the helper function to check existence

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
        await db.run(delete_query, user_id=user_id)
        return {}
    except Exception as e:
        print(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while deleting the user: {e}"
        )

# get all users
@router.get("/", response_model=List[UserInDB], status_code=status.HTTP_200_OK, summary="Get all users")
async def get_all_users_endpoint(db: AsyncSession = Depends(get_db)): 
    query = """
    MATCH (u:User)
    RETURN u.user_id AS user_id, u.name AS name, u.email AS email, u.phone AS phone, u.contact AS contact
    """
    try:
        result = await db.run(query)
        users = []
        async for record in result:
            users.append(UserInDB(
                user_id=record["user_id"],
                name=record["name"],
                email=record["email"],
                phone=record["phone"],
                contact=record.get("contact", [])
            ))

        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No users found."
            )
        return users

    except Exception as e:
        print(f"Error getting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )

@router.get("/{user_id}", response_model=UserInDB, status_code=status.HTTP_200_OK, summary="Get user details by ID")
async def get_user_details_endpoint(user_id: str, db: AsyncSession = Depends(get_db)):
    user_data = await get_user(db, user_id) 
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user_data

@router.get("/{user_id}/contacts", response_model=List[int], status_code=status.HTTP_200_OK, summary="Get contacts for a specific user")
async def get_user_contacts_endpoint(user_id: str, db: AsyncSession = Depends(get_db)): 

    query = """
    MATCH (u:User {user_id: $user_id})
    RETURN u.contact AS contacts
    """
    try:
        result = await db.run(query, user_id=user_id)
        record = await result.single()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found."
            )

        contacts = record.get("contacts")
        if contacts is None:
            return [] 

        if not isinstance(contacts, list):
            print(f"Warning: User {user_id} contact property is not a list: {type(contacts)}")
            return [] 

        return contacts

    except Exception as e:
        print(f"Error getting user contacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )

@router.put("/{user_id}/contacts", response_model=UserInDB, status_code=status.HTTP_200_OK, summary="Update contacts for a user")
async def update_user_contacts_endpoint(
    user_id: str,
    contacts_request: ContactsUploadRequest,
    db: AsyncSession = Depends(get_db)
):
    user_data = await get_user(db, user_id)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID '{user_id}' not found.")

    update_query = """
    MATCH (u:User {user_id: $user_id})
    SET u.contact = $contacts
    RETURN u.user_id AS user_id, u.name AS name, u.email AS email, u.phone AS phone, u.contact AS contact
    """
    try:
        result = await db.run(update_query, user_id=user_id, contacts=contacts_request.contacts)
        updated_user_record = await result.single()

        if not updated_user_record:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user contacts.")

        return UserInDB(
            user_id=updated_user_record["user_id"],
            name=updated_user_record["name"],
            email=updated_user_record["email"],
            phone=updated_user_record["phone"],
            contact=updated_user_record.get("contact", [])
        )
    except Exception as e:
        print(f"Error updating user contacts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An internal server error occurred: {e}")