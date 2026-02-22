from pydantic import BaseModel
from typing import Dict, Any, List, Optional
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
    user_id: UUID
    status: ApplicationStatus
    form_data: Dict[str, Any]
    created_at: datetime.datetime
    
class FormStatusResponse(BaseModel):
    form_key: str
    is_open: bool


class SendEmailRequest(BaseModel):
    to: List[str]
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    subject: str
    body: str
