from fastapi import FastAPI, Security
from auth import VerifyToken
import dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
from routers import application

dotenv.load_dotenv()

frontend_url = os.getenv("FRONTEND_URL")

app = FastAPI()
auth = VerifyToken()

app.include_router(prefix="/api", router=application.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"message": "OK"}
