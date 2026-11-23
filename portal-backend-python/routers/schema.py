from pydantic import BaseModel
from typing import Optional, Dict, Any
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
    resume_url: Optional[str] = None
    
class FormStatusResponse(BaseModel):
    form_key: str
    is_open: bool
