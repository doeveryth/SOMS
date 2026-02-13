from sqlalchemy import Text, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from ..extensions import db


class Contract(db.Model):
    __tablename__ = "Contracts"

    Contract_ID: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Person_ID: Mapped[str] = mapped_column(Text, ForeignKey('CTM_People.Person_ID'), nullable=False)

    # 계약 핵심 정보
    Service_Type: Mapped[str | None] = mapped_column(Text)  # [추가됨] 서비스 유형 (BK, CO_BA 등)
    Service_Number: Mapped[str | None] = mapped_column(Text)  # 서비스 번호
    Service_Status: Mapped[str | None] = mapped_column(Text)  # 상태
    Contract_Amount: Mapped[str | None] = mapped_column(Text)  # 계약 금액

    Open_Date: Mapped[object | None] = mapped_column(Date)  # 개통일
    Terminate_Date: Mapped[object | None] = mapped_column(Date)  # 해지일
    Contract_Note: Mapped[str | None] = mapped_column(Text)  # 비고

    Create_Date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    Deleted_YN: Mapped[str] = mapped_column(Text, default="N", nullable=False)
    Deleted_At: Mapped[datetime | None] = mapped_column(DateTime)