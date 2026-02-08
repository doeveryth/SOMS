from datetime import datetime
from sqlalchemy import Text, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class Contact(db.Model):
    __tablename__ = "Contacts"

    Contact_ID: Mapped[int] = mapped_column("Contact_ID", BigInteger, primary_key=True, autoincrement=True, quote=True)
    Person_ID: Mapped[str] = mapped_column(
        "Person_ID", Text, ForeignKey("CTM_People.Person_ID"), nullable=False, quote=True
    )

    Role_Type: Mapped[str | None] = mapped_column("Role_Type", Text, quote=True)  # 정/부
    Name: Mapped[str | None] = mapped_column("Name", Text, quote=True)

    # [추가됨] 일반전화
    General_Phone: Mapped[str | None] = mapped_column("General_Phone", Text, quote=True)

    Phone: Mapped[str | None] = mapped_column("Phone", Text, quote=True)  # 휴대폰
    Email: Mapped[str | None] = mapped_column("Email", Text, quote=True)
    Status: Mapped[str | None] = mapped_column("Status", Text, quote=True)  # 활성화/비활성화

    SMS_Receive_YN: Mapped[str | None] = mapped_column("SMS_Receive_YN", Text, quote=True)
    Report_Receive_YN: Mapped[str | None] = mapped_column("Report_Receive_YN", Text, quote=True)

    # [추가됨] 등록일 (자동생성)
    Reg_Date: Mapped[datetime | None] = mapped_column("Reg_Date", db.DateTime, default=datetime.now, quote=True)