from fastapi import FastAPI, Security
from auth import VerifyToken
from fastapi.middleware.cors import CORSMiddleware
import os
from routers import application, check_in, admin
from fastapi.staticfiles import StaticFiles
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
app.include_router(prefix="/check_in", router=check_in.router)

# Mount static files for QR code scanner UI
app.mount("/qr", StaticFiles(directory="static/qr", html=True), name="qr")


@app.get("/health")
def health():
    return {"message": "OK"}
