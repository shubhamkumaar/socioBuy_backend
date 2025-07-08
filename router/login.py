from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from config import Settings
from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from database import get_db
from neo4j import Session
from schemas.schema import UserBase, UserOut, User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
token_blacklist = set()

settings = Settings()
router = APIRouter(tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_COOKIE_NAME = "access_token"
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserOut:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: No token found in cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    query = "MATCH (u:User {email: $email}) RETURN u, id(u) AS internal_node_id"

    user_record = db.run(query, email=email).single()

    if user_record is None:
        raise credentials_exception
        
    user_data = user_record['u']
    return User(
        id=str(user_data['node_id']),
        name=user_data['name'],
        phone=user_data['phone'],
        email=user_data['email']
    )

def verify_jwt_token(token: Annotated[str,Depends(oauth2_bearer)],db: Session = Depends(get_db)):

    """This is used for in protected routes for getting the current user using the JSON Web Token which was sent under the try catch block,the payload is decoded using the jwt decode from then the user is queried fronm the database to seee if it exists and if it dosent an exception is raised and if their was error in Decoding JWT another HTTPexception is raised and if there were no errors the current user is returned"""
    print(f"Token received: {token[:30]}...") # Print first few chars
    print(f"JWT Secret Key (from settings): {settings.JWT_SECRET_KEY}")
    print(f"JWT Algorithm (from settings): {settings.JWT_ALGORITHM}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Assuming you are using a graph database like Neo4j with a similar driver
    # as in your first example. If using SQLAlchemy, the query would be different.
    query = "MATCH (u:User {email: $email}) RETURN u, id(u) AS node_id"

    user_record = db.run(query, email=email).single()
    
    if not user_record:
        raise credentials_exception
    
    user_data = user_record['u']
    if user_data is None:
        raise credentials_exception
    print(f"User data retrieved: {user_data}")
    return User(
        id=str(user_data['node_id']),
        name=user_data['name'],
        phone=user_data['phone'],
        email=user_data['email']
    )

@router.post("/login", response_model=UserOut)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db: Session = Depends(get_db)):
    query = "MATCH (u:User {email: $email}) RETURN u"
    user_record = db.run(query, email=form_data.username).single()

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user_data = user_record['u']

    if not verify_password(form_data.password, user_data['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    access_token = create_access_token(data={"sub": user_data['email']})
    return UserOut(
        success=True,
        access_token=access_token,
        message="Hello " + user_data['name'] + "!",
        name=user_data['name'],
        email=user_data['email'],
        phone=user_data['phone']
    )

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserBase, db: Session = Depends(get_db)):
    check_query = "MATCH (u:User {email: $email}) RETURN u"
    existing_user = db.run(check_query, email=user.email).single()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with the email '{user.email}' already exists."
        )

    hashed_password = get_password_hash(user.password)

    create_user_query = """
    CREATE (u:User {
        name: $name,
        phone: $phone,
        contact: $contact,
        email: $email,
        password: $password
    })
    RETURN u
    """
    params = user.model_dump()
    params["password"] = hashed_password

    try:
        result = db.run(create_user_query, params)
        created_user_record = result.single()
        user = created_user_record['u']
        return UserOut(
            success=True,
            message="Hello " + user['name'] + "!",
            name=user['name'],
            email=user['email'],
            access_token=create_access_token(data={"sub": user['email']}),
            phone=user['phone']
        )
    except Exception as e:
        print(f"ERROR: Could not register user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred during registration."
        )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
    return {"message": "Successfully logged out"}


@router.get("/users/me", response_model=UserOut)
def read_users_me(current_user: UserOut = Depends(get_current_user)):
    return current_user