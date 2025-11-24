from fastapi import FastAPI
from core.config.settings import get_database_settings
from api.routes.profile import router as profile_router

app = FastAPI(title="WB Bank")

app.include_router(profile_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "personal-cabinet"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)