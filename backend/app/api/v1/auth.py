from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.security import verify_password, create_access_token
from sqlmodel import SQLModel


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(SQLModel):
    email: str
    password: str


@router.post("/login")
def login(credentials: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.email == credentials.email)
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}