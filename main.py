from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import alembic.config
import os

from routes import orders, auth, restaurants, menus, comments, deliveries, health, menu_categories, supplements
from config.settings import settings
from middleware.error_handlers import add_error_handlers

def apply_migrations():
    """Apply database migrations at startup."""
    try:
        alembic_cfg = alembic.config.Config("alembic.ini")
        alembic.command.upgrade(alembic_cfg, "head")
    except Exception as e:
        print(f"Error applying migrations: {e}")
        # You might want to log this error or handle it differently
        # depending on your application's needs


@asynccontextmanager
async def lifespan(app: FastAPI):
    apply_migrations()
    yield


app = FastAPI(lifespan=lifespan)

# Add error handlers
add_error_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


app.include_router(orders.router, tags=["orders"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(restaurants.router, tags=["restaurants"])
app.include_router(menus.router, tags=["menus"])
app.include_router(menu_categories.router, tags=["menu-categories"])
app.include_router(supplements.router, tags=["supplements"])
app.include_router(comments.router, tags=["comments"])
app.include_router(deliveries.router, tags=["deliveries"])
app.include_router(health.router)
