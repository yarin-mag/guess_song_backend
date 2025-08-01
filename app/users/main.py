from app.core.app_factory import create_app
from app.users.routes import router as users_router

app = create_app(
    title="Users Service",
    routers=[users_router]
)



