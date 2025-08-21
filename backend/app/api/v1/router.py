from fastapi import APIRouter
from app.api.v1.endpoints import scanner, portfolio, strategies, correlation
from app.api.v1 import complexity, complexity_constraints

api_router = APIRouter()

api_router.include_router(scanner.router, prefix="/scanner", tags=["scanner"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(complexity.router, prefix="/complexity", tags=["complexity"])
api_router.include_router(complexity_constraints.router, prefix="/complexity", tags=["complexity-constraints"])
api_router.include_router(correlation.router, prefix="/correlation", tags=["correlation"])