from app.core import create_app
from app.guesses.routes import router as guesses_router

app = create_app(
    title="Guesses Service",
    routers=[guesses_router]
)