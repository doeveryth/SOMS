from sqlalchemy import Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ..extensions import db


class NoteAttachment(db.Model):
    __tablename__ = "Note_Attachments"

    Attachment_ID: Mapped[int] = mapped_column(
        "Attachment_ID", BigInteger, primary_key=True, autoincrement=True, quote=True
    )

    Note_ID: Mapped[int] = mapped_column(
        "Note_ID", BigInteger, ForeignKey("Customer_Notes.Note_ID"), nullable=False, quote=True
    )

    Original_Filename: Mapped[str] = mapped_column("Original_Filename", Text, nullable=False, quote=True)
    Stored_Filename: Mapped[str] = mapped_column("Stored_Filename", Text, nullable=False, quote=True)

    Content_Type: Mapped[str | None] = mapped_column("Content_Type", Text, quote=True)
    Size_Bytes: Mapped[int] = mapped_column("Size_Bytes", BigInteger, nullable=False, quote=True)

    Uploaded_By: Mapped[str] = mapped_column("Uploaded_By", Text, nullable=False, quote=True)  # user_id 저장
    Uploaded_At: Mapped[datetime] = mapped_column("Uploaded_At", DateTime, nullable=False, default=datetime.utcnow, quote=True)

    Deleted_YN: Mapped[str] = mapped_column("Deleted_YN", Text, nullable=False, default="N", quote=True)
    Deleted_At: Mapped[datetime | None] = mapped_column("Deleted_At", DateTime, quote=True)
