from app.core.app_factory import create_app
from app.users.routes import router as users_router
from app.guesses.routes import router as guesses_router
from app.songs.routes import router as songs_router
from app.webhooks.main import router as webhooks_router

app = create_app(
    title="Guess Song Game API",
    routers=[users_router, guesses_router, songs_router, webhooks_router],
    with_static=True
)

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, loop="asyncio")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
