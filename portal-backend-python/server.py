from fastapi import FastAPI, Security
from auth import VerifyToken
from fastapi.middleware.cors import CORSMiddleware
import os
from routers import application
import sentry_sdk
from config import Env


frontend_url = os.getenv("FRONTEND_URL")
sentry_dsn = os.getenv("SENTRY_DSN")
env = os.getenv("ENV")

if env == Env.PROD:
    sentry_sdk.init(
        dsn=sentry_dsn,
        send_default_pii=True,
    )

app = FastAPI()
auth = VerifyToken()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prefix="/application", router=application.router)


@app.get("/health")
def health():
    return {"message": "OK"}
