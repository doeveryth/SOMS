import os
from sqlalchemy import inspect  # <-- 추가됨
from werkzeug.security import generate_password_hash

from .extensions import db
from .models.user import User


def ensure_bootstrap_admin():
    admin_id = os.getenv("BOOTSTRAP_ADMIN_ID")
    admin_name = os.getenv("BOOTSTRAP_ADMIN_NAME", "Administrator")
    admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")

    if not admin_id or not admin_password:
        return

    # [수정된 부분 시작] ------------------------------------------------
    # DB 엔진을 검사하는 도구를 생성합니다.
    inspector = inspect(db.engine)

    # 'users' 테이블이 실제 DB에 있는지 확인합니다.
    # 테이블이 없다면(즉, 마이그레이션 실행 중이라면) 여기서 함수를 종료합니다.
    if not inspector.has_table("users"):
        return
    # [수정된 부분 끝] --------------------------------------------------

    existing = db.session.get(User, admin_id)
    if existing:
        return

    user = User(
        user_id=admin_id,
        user_name=admin_name,
        password_hash=generate_password_hash(admin_password),
        role="ADMIN",
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()