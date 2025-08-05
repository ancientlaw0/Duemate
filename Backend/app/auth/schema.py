from pydantic import BaseModel, Field, EmailStr, constr
from typing import Annotated, Literal, Optional 
import sqlalchemy as sa
from app import db
from app.models import User
from flask import current_app

class EmailLoginSchema(BaseModel):
    email: Annotated[EmailStr, Field(..., description="User email")]

class MobileLoginSchema(BaseModel):
    phone_number: Annotated[str, Field(..., min_length=10, max_length=13, description="User's 10-digit mobile number")]

class OtpSchema(BaseModel):
    otp: Annotated[str, Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$', description="6-digit OTP code")]
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None