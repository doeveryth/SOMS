from sqlalchemy import Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from ..extensions import db


class WorkAttachment(db.Model):
    __tablename__ = "Work_Attachments"

    Attachment_ID: Mapped[int] = mapped_column(
        "Attachment_ID", BigInteger, primary_key=True, autoincrement=True, quote=True
    )

    Work_ID: Mapped[int] = mapped_column(
        "Work_ID", BigInteger, ForeignKey("Work_Info.Work_ID"), nullable=False, quote=True
    )

    File_Name: Mapped[str] = mapped_column("File_Name", Text, nullable=False, quote=True)
    File_Path: Mapped[str] = mapped_column("File_Path", Text, nullable=False, quote=True)
    File_Size: Mapped[int] = mapped_column("File_Size", BigInteger, nullable=False, quote=True)
    Upload_Date: Mapped[datetime] = mapped_column("Upload_Date", DateTime, nullable=False, default=datetime.utcnow, quote=True)