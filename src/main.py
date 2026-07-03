from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from src.config.settings import get_settings
from src.routers.auth import router as auth_router
from src.routers.cart import router as cart_router
from src.routers.movies import router as movies_router
from src.routers.orders import router as orders_router

settings = get_settings()

OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": (
            "User registration, email activation, JWT login/logout, and token refresh. "
            "Most endpoints are public; logout requires a valid Bearer access token."
        ),
    },
    {
        "name": "Movies",
        "description": (
            "Movie catalog operations. Listing and detail views are public; "
            "creating movies requires authentication."
        ),
    },
    {
        "name": "Shopping Cart",
        "description": (
            "Authenticated cart management: view cart, add/remove items, and clear cart. "
            "Each user has exactly one cart."
        ),
    },
    {
        "name": "Orders",
        "description": (
            "Order checkout from the current user's cart. "
            "Creates a pending order with price snapshots and clears the cart."
        ),
    },
]

app = FastAPI(
    title="Online Cinema API",
    description=(
        "REST API for an online cinema platform (OpenAPI 3.x).\n\n"
        "## Authentication flow\n"
        "1. `POST /auth/register` — create account (inactive until activated)\n"
        "2. `GET /auth/activate?token=` — activate account via email token\n"
        "3. `POST /auth/activate/resend` — request a new activation token if expired\n"
        "4. `POST /auth/login` — obtain access + refresh JWT tokens\n"
        "5. `POST /auth/refresh` — rotate tokens when access token expires\n"
        "6. `POST /auth/logout?refresh_token=` — revoke refresh token (Bearer required)\n\n"
        "## Using Swagger UI\n"
        "Call `POST /auth/login`, copy `access_token`, click **Authorize**, "
        "enter `Bearer <access_token>`.\n\n"
        "## Documentation access\n"
        "Set `OPENAPI_DOCS_ENABLED=false` in `.env` to disable public docs in production."
    ),
    version="0.1.0",
    openapi_tags=OPENAPI_TAGS,
    docs_url=None,
    redoc_url=None,
)

app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(cart_router)
app.include_router(orders_router)


@app.get("/docs", include_in_schema=False)
async def swagger_docs():
    """Swagger UI — disabled when OPENAPI_DOCS_ENABLED=false."""
    if not settings.OPENAPI_DOCS_ENABLED:
        return {"detail": "API documentation is disabled."}
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_docs():
    """ReDoc UI — disabled when OPENAPI_DOCS_ENABLED=false."""
    if not settings.OPENAPI_DOCS_ENABLED:
        return {"detail": "API documentation is disabled."}
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc",
    )


@app.get("/openapi.json", include_in_schema=False)
async def openapi_json():
    """OpenAPI 3.x schema — disabled when OPENAPI_DOCS_ENABLED=false."""
    if not settings.OPENAPI_DOCS_ENABLED:
        return {"detail": "API documentation is disabled."}
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
