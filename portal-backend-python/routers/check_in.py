from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID

from db import get_db
from models.user import User
from models.check_in_log import CheckIn
from pydantic import BaseModel

router = APIRouter() #every endpoint starts with /check-in
class CheckInRequest(BaseModel):
    user_id: UUID
    event_type: str

@router.get("/test")
def test():
    return {"message": "API is working!"}

@router.post("/")
def check_in(
    payload: CheckInRequest,
    db: Session = Depends(get_db),
):
    try:
        # Try to find user id in User table 
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        name = " ".join(filter(None, [user.first_name, user.last_name]))

        # If user already checked in for this event 
        existing = (
            db.query(CheckIn)
            .filter(
                CheckIn.user_id == payload.user_id,
                CheckIn.event_type == payload.event_type,
            )
            .first()
        )
        if existing:
            message = f"{name} already checked in at {existing.check_in_time.strftime('%H:%M')}"
            
            # Return structured JSON and 400 status
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": message,
                    "user_id": str(existing.user_id),
                    "event_type": existing.event_type,
                    "check_in_time": existing.check_in_time.isoformat(),
                }
            )
        # Create check-in
        checkin = CheckIn(
            user_id=user.id,
            name=name,
            event_type=payload.event_type,
        )

        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Check-in successful",
                "user_id": str(checkin.user_id),
                "event_type": checkin.event_type,
                "check_in_time": checkin.check_in_time.isoformat(),
                "name": checkin.name,
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error: {str(e)}"}
        )

@router.post("/delete")
async def delete_log_entry(
    payload: CheckInRequest, #pass in a user_id & an event_type 
    db: Session = Depends(get_db)
):
    try:
        # Find the entry in CheckIn table
        entry = (
            db.query(CheckIn)
            .filter(
                CheckIn.user_id == payload.user_id,
                CheckIn.event_type == payload.event_type
            )
            .first()
        )

        if not entry:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Log entry not found"}
            )

        # Delete the entry
        db.delete(entry)
        db.commit()

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Log entry deleted successfully"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error: {str(e)}"}
        )