from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import auth, users, movies, watchlist, reviews

app = FastAPI(title="MovieMint")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(movies.router)
app.include_router(watchlist.router)
app.include_router(reviews.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")