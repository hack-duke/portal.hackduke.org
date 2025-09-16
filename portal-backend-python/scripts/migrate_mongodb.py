"""
EXPORT MONGODB_URI=mongodb://localhost:27017
cd portal-backend-python
python -m scripts.migrate_mongodb
"""

import os
from typing import List, Optional
from pymongo import MongoClient
from db import get_local_session
from models.user import User
from models.question import Question
from models.response import Response
from models.application import Application, ApplicationStatus


class MongoDBConnector:
    def __init__(self, connection_string: Optional[str] = None):
        self.client = None
        self.db = None
        self.connection_string = connection_string or self._get_connection_string()

    def _get_connection_string(self) -> str:
        return os.getenv("MONGODB_URI")

    def connect(self, database_name: str) -> bool:
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
            )

            self.db = self.client[database_name]

            print("Successfully connected to MongoDB")

            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")


if __name__ == "__main__":
    mongo = MongoDBConnector()

    mongo.connect("test")

    collection = mongo.db["cfg2025"]

    session = get_local_session()

    def clamp_to_int32(n: int) -> int:
        return max(-(2**31), min(2**31 - 1, n))

    def add_response(user_id, application_id, question_key, answer, type):
        if not answer:
            return

        question_id = (
            session.query(Question)
            .filter(Question.question_key == question_key)
            .first()
            .id
        )
        if (
            session.query(Response)
            .filter(Response.user_id == user_id, Response.question_id == question_id)
            .first()
        ):
            return
        print(f"Adding response for {question_key} with {answer}")
        if type == "string":
            response = Response(
                user_id=user_id,
                question_id=question_id,
                application_id=application_id,
                text_answer=answer,
            )
        elif type == "file":
            response = Response(
                user_id=user_id,
                question_id=question_id,
                application_id=application_id,
                file_s3_key=answer,
            )
        elif type == "boolean":
            response = Response(
                user_id=user_id,
                question_id=question_id,
                application_id=application_id,
                bool_answer=bool(answer),
            )
        elif type == "integer":
            response = Response(
                user_id=user_id,
                question_id=question_id,
                application_id=application_id,
                int_answer=clamp_to_int32(int(answer)),
            )
        elif type == "float":
            response = Response(
                user_id=user_id,
                question_id=question_id,
                application_id=application_id,
                float_answer=float(answer),
            )

        session.add(response)
        session.commit()

    documents = collection.find()
    for doc in documents:
        user = session.query(User).filter(User.auth0_id == doc["userId"]).first()
        if not user:
            user = User(auth0_id=doc["userId"])
            session.add(user)
            session.commit()

        application = (
            session.query(Application).filter(Application.user_id == user.id).first()
        )
        if not application:
            application = Application(user_id=user.id, form_key="2025-cfg-application")
            session.add(application)
            session.commit()

        add_response(
            user.id, application.id, "first_name", doc.get("firstName"), "string"
        )
        add_response(
            user.id, application.id, "last_name", doc.get("lastName"), "string"
        )
        add_response(
            user.id, application.id, "pref_name", doc.get("prefName"), "string"
        )
        add_response(
            user.id, application.id, "resume_key", doc.get("resumeKey"), "file"
        )
        add_response(user.id, application.id, "age", doc.get("age"), "integer")
        add_response(user.id, application.id, "country", doc.get("country"), "string")
        add_response(
            user.id, application.id, "university", doc.get("university"), "string"
        )
        add_response(user.id, application.id, "major", doc.get("major"), "string")
        add_response(
            user.id,
            application.id,
            "graduation_year",
            doc.get("graduationYear"),
            "integer",
        )
        add_response(
            user.id,
            application.id,
            "why_hackduke",
            doc.get("whyhackduke"),
            "string",
        )
        add_response(
            user.id,
            application.id,
            "why_track",
            doc.get("whytrack"),
            "string",
        )
        add_response(
            user.id,
            application.id,
            "mlh_email_permission",
            doc.get("mlh_email_permission"),
            "boolean",
        )
        add_response(
            user.id,
            application.id,
            "email",
            doc.get("email"),
            "string",
        )
        add_response(user.id, application.id, "phone", doc.get("phone"), "string")
        application.submission_json = {
            "first_name": doc.get("firstName"),
            "last_name": doc.get("lastName"),
            "pref_name": doc.get("prefName"),
            "resume_key": doc.get("resumeKey"),
            "age": doc.get("age"),
            "country": doc.get("country"),
            "university": doc.get("university"),
            "major": doc.get("major"),
            "graduation_year": doc.get("graduationYear"),
            "why_hackduke": doc.get("whyhackduke"),
            "why_track": doc.get("whytrack"),
            "mlh_email_permission": doc.get("mlh_email_permission"),
            "email": doc.get("email"),
            "phone": doc.get("phone"),
        }

        if doc.get("status") == "accepted":
            application.status = ApplicationStatus.ACCEPTED
        elif doc.get("status") == "rejected":
            application.status = ApplicationStatus.REJECTED
        elif doc.get("status") == "confirmed":
            application.status = ApplicationStatus.CONFIRMED

    mongo.disconnect()
