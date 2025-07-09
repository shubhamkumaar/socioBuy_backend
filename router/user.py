from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from database import get_db
from neo4j import AsyncSession ,Session
from schemas.schema import UserBase, User
from typing import Annotated, List,Optional
from .login import verify_jwt_token
from schemas.schema import UserBase, UserInDB, ContactsUploadRequest
from schemas.schema import OrderCreationResponse
import re
from uuid import uuid4
from utils.user import create_friend,create_order_relation

router = APIRouter(prefix="/users",tags=["User Management"])

user_dependency = Annotated[User, Depends(verify_jwt_token)]

class ContactIn(BaseModel):
    name: str
    number: str

class ImportContactsRequest(BaseModel):
    contacts: List[ContactIn] 

class ImportContactsResponse(BaseModel):
    message: str

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

def process_contact(contacts: ImportContactsRequest): 
    """
    Imports contacts from a JSON string, validates them, cleans phone numbers,
    and filters out malformed entries, helpline numbers, and invalid formats.

    Args:
        contacts_json_string (str): A JSON string containing a list of contacts.
                                    Expected format: {"contacts": [{"name": "...", "number": "..."}, ...]}

    Returns:
        dict: A dictionary containing a list of successfully processed contacts
              under the "detail" key.

    Raises:
        HTTPException: If the input string is not a valid JSON format.
    """
    
    INDIAN_MOBILE_FORMAT_PATTERN = re.compile(r"^[6-9]\d{9}$")
    processed_contacts = []

    for entry in contacts.contacts:
        # 2. Extract name and number, handling potential missing keys
        name_raw = entry.name.strip()
        number_raw = entry.number.strip()

        # 3. Validate and clean name: Must be a non-empty string after stripping whitespace
        if not isinstance(name_raw, str) or not name_raw.strip():
            continue
        name = name_raw.strip()

        # 4. Validate and clean phone number: Must be a non-empty string after stripping whitespace
        if not isinstance(number_raw, str) or not number_raw.strip():
            continue

        # Start with the raw number, stripped of leading/trailing whitespace
        current_phone_number = number_raw.strip()

        # 5. Remove '+91' prefix if present from the number *before* normalization for validation
        if current_phone_number.startswith('+91'):
            current_phone_number = current_phone_number[3:].strip() # Remove '+91' and strip any extra whitespace

        # 6. Normalize phone number to digits only for validation and helpline check
        normalized_phone_number = re.sub(r'\D', '', current_phone_number)

        # 7. Validate phone number format (10 digits, starts with 6-9)
        if not INDIAN_MOBILE_FORMAT_PATTERN.match(normalized_phone_number):
            continue

        # If all checks pass, add to the list of processed contacts
        # The 'current_phone_number' now holds the cleaned 10-digit number without +91
        processed_contacts.append({'name': name, 'number': current_phone_number})
        # print(f"Successfully processed contact: Name='{name}', Number='{current_phone_number}'")
    return {"detail": processed_contacts}

@router.post("/import_contacts", status_code=status.HTTP_201_CREATED)
def import_contacts(contact: ImportContactsRequest, user: user_dependency, db: Session = Depends(get_db)):
    contacts = process_contact(contact)
    
    save_contacts_query = """    MATCH (u:User {phone: $phone})
    SET u.contact = $contacts
    RETURN u.contact AS contact
    """
    try:
        result = db.run(save_contacts_query, phone=user.phone, contacts=contacts['detail'])
        updated_contacts = result.single()
        if not updated_contacts:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update contacts in the database."
            )
    except Exception as e:
        print(f"Error saving contacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred while saving contacts: {e}"
        )
    
    create_contact_list = [
        contact['number'] for contact in contacts['detail']
    ]
    create_contact_list.remove(user.phone) if user.phone in create_contact_list else None
    create_friend(create_contact_list,user.phone,db)


    return {"message": "Contacts processed successfully"}
    
@router.post("/create_order", response_model=OrderCreationResponse, status_code=status.HTTP_201_CREATED, summary="Create a new order")
def create_order_endpoint(order_data: List[str], user: user_dependency, db: Session = Depends(get_db)) -> OrderCreationResponse: # Changed return type to OrderCreationResponse
    if not order_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order data cannot be empty."
        )

    return create_order_relation(order_data, user, db)