from datetime import datetime, date

from sqlalchemy import Text, BigInteger, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class SRTicket(db.Model):
    __tablename__ = "SR_Tickets"

    sr_id: Mapped[int] = mapped_column(
        "SR_ID", BigInteger, primary_key=True, autoincrement=True, quote=True
    )

    location: Mapped[str] = mapped_column("Location", Text, nullable=False, quote=True)
    company: Mapped[str] = mapped_column("Company", Text, nullable=False, quote=True)

    # 구분 / 등급 / 요청자
    category: Mapped[str | None] = mapped_column("Category", Text, quote=True)
    severity: Mapped[str | None] = mapped_column("Severity", Text, quote=True)
    requester: Mapped[str | None] = mapped_column("Requester", Text, quote=True)

    request_date: Mapped[date] = mapped_column("Request_Date", Date, nullable=False, quote=True)

    content: Mapped[str] = mapped_column("Content", Text, nullable=False, quote=True)

    handler: Mapped[str] = mapped_column("Handler", Text, nullable=False, quote=True)
    handled_date: Mapped[date | None] = mapped_column("Handled_Date", Date, quote=True)

    result: Mapped[str | None] = mapped_column("Result", Text, quote=True)
    remark: Mapped[str | None] = mapped_column("Remark", Text, quote=True)

    created_by: Mapped[str] = mapped_column("Created_By", Text, nullable=False, quote=True)
    created_at: Mapped[datetime] = mapped_column(
        "Created_At", DateTime, nullable=False, default=datetime.utcnow, quote=True
    )

    updated_by: Mapped[str | None] = mapped_column("Updated_By", Text, quote=True)
    updated_at: Mapped[datetime | None] = mapped_column("Updated_At", DateTime, quote=True)