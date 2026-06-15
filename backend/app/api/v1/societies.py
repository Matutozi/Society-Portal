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