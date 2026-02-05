from sqlalchemy import Text, BigInteger, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from ..extensions import db


class Contract(db.Model):
    __tablename__ = "Contracts"

    Contract_ID: Mapped[int] = mapped_column("Contract_ID", BigInteger, primary_key=True, autoincrement=True, quote=True)
    Person_ID: Mapped[str] = mapped_column(
        "Person_ID", Text, ForeignKey('CTM_People.Person_ID'), nullable=False, quote=True
    )

    Contract_Name: Mapped[str | None] = mapped_column("Contract_Name", Text, quote=True)
    Contract_Amount: Mapped[object | None] = mapped_column("Contract_Amount", Numeric(18, 2), quote=True)
    Currency: Mapped[str | None] = mapped_column("Currency", Text, quote=True)

    Contract_Start_Date: Mapped[object | None] = mapped_column("Contract_Start_Date", Date, quote=True)
    Contract_End_Date: Mapped[object | None] = mapped_column("Contract_End_Date", Date, quote=True)

    Contract_Notes: Mapped[str | None] = mapped_column("Contract_Notes", Text, quote=True)

    Submitter: Mapped[str] = mapped_column("Submitter", Text, nullable=False, quote=True)
    Create_Date: Mapped[datetime] = mapped_column("Create_Date", DateTime, nullable=False, default=datetime.utcnow, quote=True)

    Updater: Mapped[str | None] = mapped_column("Updater", Text, quote=True)
    Update_Date: Mapped[datetime | None] = mapped_column("Update_Date", DateTime, quote=True)

    Deleted_YN: Mapped[str] = mapped_column("Deleted_YN", Text, nullable=False, default="N", quote=True)
    Deleted_At: Mapped[datetime | None] = mapped_column("Deleted_At", DateTime, quote=True)