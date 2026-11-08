import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Security
from auth import VerifyToken
from fastapi.middleware.cors import CORSMiddleware
import os
from routers import application, check_in, admin, roles, events
from fastapi.staticfiles import StaticFiles
import sentry_sdk
from config import Env
from db import get_local_session
from services.event_notifications import (
    WebPushSettings,
    send_due_event_notifications,
)


frontend_url = os.getenv("FRONTEND_URL")
sentry_dsn = os.getenv("SENTRY_DSN")
env = os.getenv("ENV")
logger = logging.getLogger(__name__)

if env == Env.PROD:
    sentry_sdk.init(
        dsn=sentry_dsn,
        send_default_pii=False,
    )


def _deliver_due_notifications() -> None:
    db = get_local_session()
    try:
        counts = send_due_event_notifications(db)
        if counts["due"]:
            logger.info(
                "Event notification cycle complete due=%s sent=%s failed=%s disabled=%s",
                counts["due"],
                counts["sent"],
                counts["failed"],
                counts["disabled"],
            )
    finally:
        db.close()


async def _notification_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(_deliver_due_notifications)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.error(
                "Event notification cycle failed error_type=%s",
                type(error).__name__,
            )
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = None
    try:
        if WebPushSettings.from_environment().enabled:
            task = asyncio.create_task(_notification_loop())
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(lifespan=lifespan)
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
app.include_router(prefix="/admin", router=admin.router)
app.include_router(prefix="/roles", router=roles.router)
app.include_router(prefix="/events", router=events.router)

# Mount static files for QR code scanner UI
app.mount("/qr", StaticFiles(directory="static/qr", html=True), name="qr")


@app.get("/health")
def health():
    return {"message": "OK"}
