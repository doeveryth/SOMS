from datetime import datetime, date

from sqlalchemy import Text, BigInteger, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class WorkInfo(db.Model):
    __tablename__ = "Work_Info"

    Work_ID: Mapped[int] = mapped_column(
        "Work_ID", BigInteger, primary_key=True, autoincrement=True, quote=True
    )

    Person_ID: Mapped[str] = mapped_column(
        "Person_ID", Text, ForeignKey("CTM_People.Person_ID"), nullable=False, quote=True
    )

    Work_Type: Mapped[str | None] = mapped_column("Work_Type", Text, quote=True)
    Work_Date: Mapped[date | None] = mapped_column("Work_Date", Date, quote=True)
    Summary: Mapped[str | None] = mapped_column("Summary", Text, quote=True)
    Description: Mapped[str | None] = mapped_column("Description", Text, quote=True)

    Submitter: Mapped[str] = mapped_column("Submitter", Text, nullable=False, quote=True)
    Create_Date: Mapped[datetime] = mapped_column(
        "Create_Date", DateTime, nullable=False, default=datetime.utcnow, quote=True
    )

    Attachment_YN: Mapped[str] = mapped_column("Attachment_YN", Text, nullable=False, default="N", quote=True)

    people = relationship("CTMPeople", back_populates="work_items")