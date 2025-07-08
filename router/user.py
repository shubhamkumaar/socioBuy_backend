from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from database import get_db
from neo4j import Session
from schemas.schema import UserBase, User
from typing import Annotated, List
from .login import verify_jwt_token
from schemas.schema import UserBase
import json
import re
router = APIRouter()

user_dependency = Annotated[User, Depends(verify_jwt_token)]

class ContactIn(BaseModel):
    name: str
    number: str

class ImportContactsRequest(BaseModel):
    contacts: List[ContactIn] 

class ImportContactsResponse(BaseModel):
    message: str

@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserBase, db: Session = Depends(get_db)):

    check_query = """
    MATCH (u:User)
    WHERE u.name = $name OR u.email = $email
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
        name: $name,
        phone: $phone,
        contact: $contact,
        email: $email
    })
    RETURN u
    """
    params = {
        "name": user.name,
        "phone": user.phone,
        "contact": user.contact,
        "email": user.email
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



#get user contacts list from user contacts
@router.get("/get_user_contacts", status_code=status.HTTP_200_OK)
def get_user_contacts(user_contact: str, db: Session = Depends(get_db)):

    query = """
    MATCH (u:User)
    SET u.contact = $newContacts 
    RETURN u
    """

    parameters = {
            "newContacts": user_contact
        }
    try:
        result = db.run(query, parameters)
        updated_user = result.single()
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        
        return updated_user.data()['u']
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {e}"
        )

def process_contact(contacts: ImportContactsRequest): # Renamed parameter for clarity
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
    create_contact_list = [
        contact['number'] for contact in contacts['detail']
    ]
    print(create_contact_list)

    # Add this in database
    return {"message": "Contacts processed successfully"}
    
