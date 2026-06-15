from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Optional
from app.database import get_session
from app.models import Society, ExecutiveContact, SocietyCategory


router = APIRouter(prefix="/api/v1/societies", tags=["societies"])


@router.get("/")
def list_societies(
    category: Optional[SocietyCategory] = None,
    session: Session = Depends(get_session),
):
    query = select(Society)
    if category is not None:
        query = query.where(Society.category == category)
    societies = session.exec(query).all()
    return societies


@router.get("/{slug}")
def get_society(slug: str, session: Session = Depends(get_session)):
    society = session.exec(
        select(Society).where(Society.slug == slug)
    ).first()

    if society is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Society not found",
        )
    contacts = session.exec(
        select(ExecutiveContact)
        .where(ExecutiveContact.society_id == society.id)
        .order_by(ExecutiveContact.order_weight)
    ).all()
    return {"society": society, "executives": contacts}


from typing import Optional
from app.models import SocietyAdmin, User, UserRole
from app.security import get_current_user
from sqlmodel import SQLModel
import uuid


class SocietyUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[SocietyCategory] = None
    logo_url: Optional[str] = None
    registration_url: Optional[str] = None
    whatsapp_link: Optional[str] = None


@router.put("/{society_id}")
def update_society(
    society_id: uuid.UUID,
    update_data: SocietyUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    society = session.get(Society, society_id)
    if society is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Society not found",
        )

    if current_user.role == UserRole.COMMUNITY_ADMIN:
        membership = session.exec(
            select(SocietyAdmin).where(
                SocietyAdmin.user_id == current_user.id,
                SocietyAdmin.society_id == society_id,
            )
        ).first()
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit societies you administer",
            )

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(society, key, value)

    session.add(society)
    session.commit()
    session.refresh(society)
    return society