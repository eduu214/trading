from fastapi import APIRouter
from app.api.v1.endpoints import scanner, strategies, portfolio

api_router = APIRouter()

api_router.include_router(scanner.router, prefix="/scanner", tags=["scanner"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])