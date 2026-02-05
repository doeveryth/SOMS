from sqlalchemy import Text, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class AccessDetails(db.Model):
    __tablename__ = "Access_Details"

    Access_ID: Mapped[int] = mapped_column("Access_ID", BigInteger, primary_key=True, autoincrement=True, quote=True)
    Person_ID: Mapped[str] = mapped_column(
        "Person_ID", Text, ForeignKey("CTM_People.Person_ID"), nullable=False, quote=True
    )

    Login_ID: Mapped[str | None] = mapped_column("Login_ID", Text, quote=True)
    Password_Hash: Mapped[str | None] = mapped_column("Password_Hash", Text, quote=True)
    Token: Mapped[str | None] = mapped_column("Token", Text, quote=True)
    License_Type: Mapped[str | None] = mapped_column("License_Type", Text, quote=True)
    Access_Restrictions: Mapped[str | None] = mapped_column("Access_Restrictions", Text, quote=True)

    sp_secure_dashboard_link__c: Mapped[str | None] = mapped_column("sp_secure_dashboard_link__c", Text, quote=True)
    sp_issue_dashboard_link__c: Mapped[str | None] = mapped_column("sp_issue_dashboard_link__c", Text, quote=True)