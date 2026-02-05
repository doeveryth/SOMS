from sqlalchemy import Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ..extensions import db


class CustomerNote(db.Model):
    __tablename__ = "Customer_Notes"

    Note_ID: Mapped[int] = mapped_column("Note_ID", BigInteger, primary_key=True, autoincrement=True, quote=True)

    Person_ID: Mapped[str] = mapped_column(
        "Person_ID", Text, ForeignKey("CTM_People.Person_ID"), nullable=False, quote=True
    )

    Severity: Mapped[str] = mapped_column("Severity", Text, nullable=False, quote=True)  # P1/P2/P3
    Tags: Mapped[str] = mapped_column("Tags", Text, nullable=False, quote=True)          # CSV (e.g., "보안,백업")
    Content: Mapped[str] = mapped_column("Content", Text, nullable=False, quote=True)

    Created_By: Mapped[str] = mapped_column("Created_By", Text, nullable=False, quote=True)  # user_id 저장
    Created_At: Mapped[datetime] = mapped_column("Created_At", DateTime, nullable=False, default=datetime.utcnow, quote=True)

    Updated_By: Mapped[str | None] = mapped_column("Updated_By", Text, quote=True)
    Updated_At: Mapped[datetime | None] = mapped_column("Updated_At", DateTime, quote=True)

    Deleted_YN: Mapped[str] = mapped_column("Deleted_YN", Text, nullable=False, default="N", quote=True)
    Deleted_By: Mapped[str | None] = mapped_column("Deleted_By", Text, quote=True)
    Deleted_At: Mapped[datetime | None] = mapped_column("Deleted_At", DateTime, quote=True)

    people = relationship("CTMPeople", back_populates="notes")
    attachments = relationship("NoteAttachment", back_populates="note", lazy="dynamic")