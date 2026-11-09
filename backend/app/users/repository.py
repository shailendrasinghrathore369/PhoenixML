import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user_in: UserCreate, hashed_password: str) -> User:
        db_user = User(
            full_name=user_in.full_name,
            email=user_in.email,
            username=user_in.username,
            hashed_password=hashed_password,
            role=user_in.role,
            is_active=user_in.is_active,
            is_verified=user_in.is_verified,
        )
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_users(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        stmt = select(User).offset(skip).limit(limit)
        return self.session.execute(stmt).scalars().all()

    def update_user(self, db_user: User, user_in: UserUpdate, hashed_password: Optional[str] = None) -> User:
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            del update_data["password"]
            
        if hashed_password:
            update_data["hashed_password"] = hashed_password

        for field, value in update_data.items():
            setattr(db_user, field, value)

        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user

    def delete_user(self, db_user: User) -> None:
        self.session.delete(db_user)
        self.session.commit()
