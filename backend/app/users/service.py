from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import UserProfileUpdate, UserPasswordChange
from app.auth.security import get_password_hash, verify_password
from app.auth.exceptions import AuthenticationError

class UserService:
    def __init__(self, db: Session = Depends(get_db)):
        self.repo = UserRepository(db)

    def update_profile(self, user: User, profile_data: UserProfileUpdate) -> User:
        update_dict = profile_data.model_dump(exclude_unset=True)
        
        # Check uniqueness constraints
        if "username" in update_dict and update_dict["username"] != user.username:
            if self.repo.get_by_username(update_dict["username"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already registered"
                )
                
        if "email" in update_dict and update_dict["email"] != user.email:
            if self.repo.get_by_email(update_dict["email"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
                
        # Manually update fields instead of using UserUpdate because 
        # UserUpdate allows updating role and active status. 
        # Here we strictly enforce that only profile fields are updated.
        for field, value in update_dict.items():
            setattr(user, field, value)
            
        self.repo.session.add(user)
        self.repo.session.commit()
        self.repo.session.refresh(user)
        return user

    def change_password(self, user: User, password_data: UserPasswordChange) -> dict:
        if not verify_password(password_data.current_password, user.hashed_password):
            raise AuthenticationError("Incorrect current password")
            
        new_hashed_password = get_password_hash(password_data.new_password)
        user.hashed_password = new_hashed_password
        
        self.repo.session.add(user)
        self.repo.session.commit()
        
        return {
            "message": "Password updated successfully. Existing tokens remain valid until expiration."
        }
