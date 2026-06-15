from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, select
from app.database import get_session
from app.models import SocietyAdmin, UrgencyLevel, User, UserRole, WelfarePost, WelfarePostCategory
from app.security import get_current_user


router = APIRouter(prefix="/api/v1/welfare", tags=["welfare"])

class WelfarePostCreate(SQLModel):
    society_id: Optional[uuid.UUID] = None
    title: str
    content: str
    category: WelfarePostCategory
    attachment_url: Optional[str] = None
    is_pinned: bool = False
    urgency_level: UrgencyLevel = UrgencyLevel.LOW
    
@router.get("/")
def list_welfare_posts(
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session),
):
    query = (
        select(WelfarePost)
        .order_by(
            WelfarePost.is_pinned.desc(),
            WelfarePost.urgency_level.desc(),
            WelfarePost.created_at.desc(),
        )
        .offset(skip)
        .limit(limit)
    )
    posts = session.exec(query).all()
    return posts


@router.post("/")
def create_welfare_post(
    post_data: WelfarePostCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Rule 1: only super_admin can post a global bulletin (no society_id)
    if post_data.society_id is None:
        if current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can create global bulletins",
            )
    else:
        # Rule 2: community_admin may only post under a society they administer
        if current_user.role == UserRole.COMMUNITY_ADMIN:
            membership = session.exec(
                select(SocietyAdmin).where(
                    SocietyAdmin.user_id == current_user.id,
                    SocietyAdmin.society_id == post_data.society_id,
                )
            ).first()
            if membership is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only post under societies you administer",
                )

    post = WelfarePost(
        society_id=post_data.society_id,
        title=post_data.title,
        content=post_data.content,
        category=post_data.category,
        attachment_url=post_data.attachment_url,
        is_pinned=post_data.is_pinned,
        urgency_level=post_data.urgency_level,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post

