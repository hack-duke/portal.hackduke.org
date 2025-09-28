from pydantic import BaseModel
from typing import Dict, Any
import datetime
from uuid import UUID
from models.application import ApplicationStatus


class SubmitApplicationRequest(BaseModel):
    form_key: str
    form_data: Dict[str, Any]


class SubmitApplicationResponse(BaseModel):
    applicationId: UUID


class GetApplicationResponse(BaseModel):
    id: UUID
    status: ApplicationStatus
    form_data: Dict[str, Any]
    created_at: datetime.datetime
