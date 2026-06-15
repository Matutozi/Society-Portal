import json
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import User, Society, SocietyAdmin, ExecutiveContact, WelfarePost, UserRole
from app.security import get_password_hash, verify_password
from app.config import settings

def seed():
    create_db_and_tables()

    with open("seed.json") as f:
        data = json.load(f)
    
    with Session(engine) as session:
        for soc in data["societies"]:
            existing = session.exec(select(Society).where(Society.slug == soc["slug"])).first()
            if existing:
                print(f"Skipping {soc['slug']}, already exists")   
                continue
            society = Society(
                name=soc["name"],
                slug = soc["slug"],
                category = soc["category"],
                description =soc["description"]
            )
            session.add(society)
            session.commit()
            session.refresh(society)

            for exec_data in soc.get("executives", []):
                contact = ExecutiveContact(
                    society_id=society.id,
                    name=exec_data["name"],
                    role=exec_data["role"],
                    email=exec_data.get("email"),
                    order_weight=exec_data.get("order_weight", 0),
                )
                session.add(contact)
            session.commit()
            print(f"Created {soc['slug']}")

        existing_admin = session.exec(
        select(User).where(User.role == UserRole.SUPER_ADMIN)).first()

        if existing_admin:
            print("Super admin already exists, skipping")
        else:
            admin = User(
                email=settings.SUPER_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.SUPER_ADMIN_PASSWORD),
                role=UserRole.SUPER_ADMIN,
                is_active=True,
            )
            session.add(admin)
            session.commit()
            print(f"Created super admin: {settings.SUPER_ADMIN_EMAIL}")


if __name__ == "__main__":
    seed()
