from fastapi import APIRouter
from app.api.v1 import auth, organizations, projects, queues, jobs, workers

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(queues.router, tags=["Queues"])
api_router.include_router(jobs.router, tags=["Jobs"])
api_router.include_router(workers.router, prefix="/workers", tags=["Workers"])

