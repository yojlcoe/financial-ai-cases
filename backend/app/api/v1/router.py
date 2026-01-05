from fastapi import APIRouter

from app.api.v1 import companies, articles, jobs, settings, reports, search_settings, prompts

api_router = APIRouter()

api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["companies"]
)

api_router.include_router(
    articles.router,
    prefix="/articles",
    tags=["articles"]
)

api_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["jobs"]
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"]
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"]
)

api_router.include_router(
    search_settings.router,
    tags=["search-settings"]
)

api_router.include_router(
    prompts.router,
    tags=["prompts"]
)
