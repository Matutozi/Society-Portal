import uuid

from enum import IntEnum, Enum
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    COMMUNITY_ADMIN = "community_admin"

class UrgencyLevel(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole
    is_active: bool = Field(default=True)

class SocietyCategory(str, Enum):
    ACADEMIC = "academic"
    TECHNOLOGICAL = "technological"
    CULTURAL = "cultural"
    HUMANITARIAN = "humanitarian"
    SPORTS = "sports"


class WelfarePostCategory(str, Enum):
    WELFARE = "welfare"
    ACADEMIC_ANNOUNCEMENT = "academic_announcement"
    STUDY_MATERIAL = "study_material"
    EMERGENCY = "emergency"



class Society(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    slug: str = Field(unique=True, index=True)
    category: SocietyCategory
    description: str
    logo_url: Optional[str] = Field(default=None)
    registration_url: Optional[str] = Field(default=None)
    whatsapp_link: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SocietyAdmin(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id:uuid.UUID = Field(foreign_key="user.id")
    society_id:uuid.UUID = Field(foreign_key="society.id")

class ExecutiveContact(SQLModel, table=True):
    id:uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    society_id: uuid.UUID = Field(foreign_key="society.id")
    name:str 
    role:str
    email: Optional[str] = Field(default=None)
    whatsapp_link: Optional[str] = Field(default=None)
    order_weight:int = Field(default=0)


class WelfarePost(SQLModel, table=True):
    id:uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    society_id: Optional[uuid.UUID] = Field(foreign_key="society.id", default=None, nullable=True)
    title:str
    content:str
    category: WelfarePostCategory
    attachment_url: Optional[str] = Field(default=None)
    is_pinned:bool = Field(default=False, index=True)
    urgency_level: UrgencyLevel = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)



