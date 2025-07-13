from fastapi import FastAPI, APIRouter
from router.user import router as user_router 
from router.login import router as login_router
from router.order import router as order_router
from router.product import router as product_router 
from router.home import router as home_page
from router.cart import router as cart_router
app = FastAPI(title="socioBuy API", version="1.0.0")

router = APIRouter(prefix="/api")

router.include_router(home_page)

router.include_router(user_router)

router.include_router(login_router)

router.include_router(order_router)

router.include_router(product_router)

router.include_router(cart_router)

app.include_router(router)