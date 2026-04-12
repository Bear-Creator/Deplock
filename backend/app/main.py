from app.api.v1.projects import router as projects_router
from fastapi import FastAPI

app = FastAPI(title="Deplock Control Plane API")

# Регистрация v1 API роутеров
app.include_router(projects_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}
