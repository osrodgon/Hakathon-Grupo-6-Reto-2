from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    profile_type: Optional[str] = None  # "parent"|"child"
    has_mobility_issues: bool = False
    age_range: Optional[str] = None     # "4-6"|"7-9"|"10-12"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserLocation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    latitude: float
    longitude: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

class POI(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    latitude: float
    longitude: float
    kids_friendly: bool = True
    accessible: bool = True
    short: Optional[str] = None
    source: Optional[str] = None
