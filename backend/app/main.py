"""
Mobyar API (FastAPI)
Phase 3 - Practical implementation

This API is designed for a single shop (single center) and exposes endpoints for:
- Auth (login/me)
- CRUD: categories, products, services
- Sales workflow: create sale, add items, finalize sale
- Repairs workflow: create repair order, update status
- Reports: daily sales, low stock, open repairs
- Extra demo helpers: list customers, list customer phones (for UI forms)

Database schema is created via SQL scripts under /sql in the project root.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, categories, products, services, sales, repairs, reports, users

app = FastAPI(
    title="Mobyar API",
    version="1.0.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
)

# CORS (for React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(categories.router, prefix=settings.api_v1_prefix)
app.include_router(products.router, prefix=settings.api_v1_prefix)
app.include_router(services.router, prefix=settings.api_v1_prefix)
app.include_router(sales.router, prefix=settings.api_v1_prefix)
app.include_router(repairs.router, prefix=settings.api_v1_prefix)
app.include_router(reports.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    """Simple health check."""
    return {"status": "ok"}
