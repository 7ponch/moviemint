from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int
    username: str
    email: str


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    email: Optional[EmailStr] = None