from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    bloodGroup: Optional[str] = Field(None, alias="bloodGroup")
    age: Optional[int] = None
    gender: Optional[str] = None
    avatarUrl: Optional[str] = Field(None, alias="avatarUrl")
    familyMembers: Optional[List[Dict[str, Any]]] = None

    class Config:
        populate_by_name = True

class LoginNotifyRequest(BaseModel):
    recipientEmail: Optional[str] = None
    userName: Optional[str] = None
    device: Optional[str] = None
    ipAddress: Optional[str] = None

class OTPRequest(BaseModel):
    email: str
    purpose: Optional[str] = "login"

class OTPVerifyRequest(BaseModel):
    email: str
    code: str
