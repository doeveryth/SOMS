from sqlalchemy import Text, Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class CTMPeople(db.Model):
    __tablename__ = "CTM_People"

    CTM_ID: Mapped[int] = mapped_column("CTM_ID", Integer, primary_key=True, autoincrement=True, quote=True)

    Person_ID: Mapped[str] = mapped_column("Person_ID", Text, unique=True, nullable=False, quote=True)

    Company: Mapped[str | None] = mapped_column("Company", Text, quote=True)
    Last_Name: Mapped[str | None] = mapped_column("Last_Name", Text, quote=True)

    Customer_Name: Mapped[str | None] = mapped_column("Customer_Name", Text, quote=True)
    Service_Type: Mapped[str | None] = mapped_column("Service_Type", Text, quote=True)
    Client_Type: Mapped[str | None] = mapped_column("Client_Type", Text, quote=True)
    Open_Date: Mapped[object | None] = mapped_column("Open_Date", Date, quote=True)
    Terminate_Date: Mapped[object | None] = mapped_column("Terminate_Date", Date, quote=True)

    chHistory: Mapped[str | None] = mapped_column("chHistory", Text, quote=True)
    chEtc: Mapped[str | None] = mapped_column("chEtc", Text, quote=True)
    Sales_Manager: Mapped[str | None] = mapped_column("Sales_Manager", Text, quote=True)

    contract_memo__c: Mapped[str | None] = mapped_column("contract_memo__c", Text, quote=True)
    Service_Contract_Amount__c: Mapped[str | None] = mapped_column("Service_Contract_Amount__c", Text, quote=True)

    Service_Number: Mapped[str | None] = mapped_column("Service_Number", Text, quote=True)
    Service_Status: Mapped[str | None] = mapped_column("Service_Status", Text, quote=True)
    IDC: Mapped[str | None] = mapped_column("IDC", Text, quote=True)
    Rack_Location: Mapped[str | None] = mapped_column("Rack_Location", Text, quote=True)
    Client_Sensitivity: Mapped[str | None] = mapped_column("Client_Sensitivity", Text, quote=True)
    Report_YN: Mapped[str | None] = mapped_column("Report_YN", Text, quote=True)

    Customer_Folder: Mapped[str | None] = mapped_column("Customer_Folder", Text, quote=True)
    Customer_Folder_Detail: Mapped[str | None] = mapped_column("Customer_Folder_Detail", Text, quote=True)

    Service_URL__c: Mapped[str | None] = mapped_column("Service_URL__c", Text, quote=True)

    Business_Type: Mapped[str | None] = mapped_column("Business_Type", Text, quote=True)
    Business_Detail: Mapped[str | None] = mapped_column("Business_Detail", Text, quote=True)

    Backup_Service: Mapped[str | None] = mapped_column("Backup_Service", Text, quote=True)
    Backup_Type: Mapped[str | None] = mapped_column("Backup_Type", Text, quote=True)
    Backup_Period: Mapped[str | None] = mapped_column("Backup_Period", Text, quote=True)
    Backup_Path: Mapped[str | None] = mapped_column("Backup_Path", Text, quote=True)

    Vaccine__c: Mapped[str | None] = mapped_column("Vaccine__c", Text, quote=True)
    ShellMonitor__c: Mapped[str | None] = mapped_column("ShellMonitor__c", Text, quote=True)

    Other_Info: Mapped[str | None] = mapped_column("Other_Info", Text, quote=True)

    notes = relationship("CustomerNote", back_populates="people", lazy="dynamic")
    work_items = relationship("WorkInfo", back_populates="people", lazy="dynamic")