# Generic router module for the Databricks app template
# Add your FastAPI routes here

from fastapi import APIRouter

from .query import router as query_router
from .user import router as user_router

router = APIRouter()
router.include_router(user_router, prefix='/user', tags=['user'])
router.include_router(query_router, prefix='', tags=['query'])
