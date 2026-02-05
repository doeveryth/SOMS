from flask_login import UserMixin
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from ..extensions import login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False, default="USER")  # ADMIN/USER
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def get_id(self):
        return self.user_id


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, user_id)

