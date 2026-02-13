from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from ..extensions import login_manager


class User(db.Model, UserMixin):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False, default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # [추가됨] 이메일, 부서, 생성일 추가
    email: Mapped[str] = mapped_column(String(120), nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def get_id(self):
        return self.user_id


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, user_id)