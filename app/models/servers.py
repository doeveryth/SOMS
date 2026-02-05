from sqlalchemy import Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class ServerInfo(db.Model):
    __tablename__ = "Server_Info"

    Server_ID: Mapped[int] = mapped_column("Server_ID", BigInteger, primary_key=True, autoincrement=True, quote=True)
    Person_ID: Mapped[str] = mapped_column(
        "Person_ID", Text, ForeignKey("CTM_People.Person_ID"), nullable=False, quote=True
    )

    chServerName: Mapped[str | None] = mapped_column("chServerName", Text, quote=True)
    chServerInfo: Mapped[str | None] = mapped_column("chServerInfo", Text, quote=True)
    Submitter: Mapped[str | None] = mapped_column("Submitter", Text, quote=True)
    Create_Date: Mapped[object | None] = mapped_column("Create_Date", DateTime, quote=True)