from fastapi import FastAPI
from router.user import router as user_router 
from router.login import router as login_router
from router.order import router as order_router
from router.product import router as product_router 
from router.home import router as home_page

app = FastAPI()


app.include_router(home_page)

app.include_router(user_router)

app.include_router(login_router)

app.include_router(order_router)

app.include_router(product_router)
