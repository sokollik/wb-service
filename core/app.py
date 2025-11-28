from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.api.v1.v1 import v1_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)
