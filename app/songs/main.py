from app.core import create_app
from app.songs.routes import router as songs_router

app = create_app(
    title="Songs Service",
    routers=[songs_router]
)