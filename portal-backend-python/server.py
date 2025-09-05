from fastapi import FastAPI, Security
from auth import VerifyToken
import dotenv
from fastapi.middleware.cors import CORSMiddleware
import os

dotenv.load_dotenv()

frontend_url = os.getenv("FRONTEND_URL")

app = FastAPI()
auth = VerifyToken()


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


@app.get("/api/applications")
def get_applications(auth_response: str = Security(auth.verify)):
    return auth_response
