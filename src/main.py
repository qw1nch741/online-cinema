from src.routers.movies import router as movies_router

app = FastAPI()


app.include_router(movies_router)
