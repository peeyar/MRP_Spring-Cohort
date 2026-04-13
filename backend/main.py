"""WarmPath MVP — FastAPI entry point."""

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(name)s — %(message)s")

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tracing import setup_tracing, instrument_app

setup_tracing()

app = FastAPI(title="WarmPath MVP")
instrument_app(app)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://warm-path-beta.vercel.app",
    "http://3.215.104.193",
    "http://mywarmpath.com",
    "https://mywarmpath.com",
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
