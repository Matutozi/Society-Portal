from sqlmodel import Session, select
from app.database import engine
from app.models import User, Society, SocietyAdmin, UserRole
from app.security import get_password_hash


def create_test_community_admin():
    with Session(engine) as session:
        # Check if the test admin already exists
        existing = session.exec(
            select(User).where(User.email == "community@test.com")
        ).first()
        if existing:
            print("Test community admin already exists")
            admin = existing
        else:
            admin = User(
                email="community@test.com",
                hashed_password=get_password_hash("testpass123"),
                role=UserRole.COMMUNITY_ADMIN,
                is_active=True,
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print(f"Created community admin: {admin.email} (id: {admin.id})")

        # Link them to ONE society (the first one)
        first_society = session.exec(select(Society)).first()
        if first_society is None:
            print("No societies found, run seed.py first")
            return

        link_exists = session.exec(
            select(SocietyAdmin).where(
                SocietyAdmin.user_id == admin.id,
                SocietyAdmin.society_id == first_society.id,
            )
        ).first()

        if link_exists:
            print(f"Link already exists for society: {first_society.name}")
        else:
            link = SocietyAdmin(user_id=admin.id, society_id=first_society.id)
            session.add(link)
            session.commit()
            print(f"Linked admin to society: {first_society.name} (id: {first_society.id})")

        # Print the OTHER societies they should NOT be able to post under
        all_societies = session.exec(select(Society)).all()
        print("\n--- Test data summary ---")
        print(f"Community admin email: community@test.com / password: testpass123")
        print(f"ADMINISTERS (can post): {first_society.name} -> {first_society.id}")
        for soc in all_societies:
            if soc.id != first_society.id:
                print(f"DOES NOT administer (should get 403): {soc.name} -> {soc.id}")


if __name__ == "__main__":
    create_test_community_admin()