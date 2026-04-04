"""WarmPath MVP — FastAPI entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WarmPath MVP")

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://warm-path-beta.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

from api import router as api_router

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
