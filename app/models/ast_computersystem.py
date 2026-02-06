from app import db
from sqlalchemy import event
import re
from datetime import datetime


class AST_Computer_System(db.Model):
    __tablename__ = 'AST_Computer_System'
    __table_args__ = {'extend_existing': True}

    # 기본 식별 및 참조
    Asset_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Person_ID = db.Column(db.Text, db.ForeignKey('CTM_People.Person_ID'), nullable=False)
    Company = db.Column(db.Text)
    Owner_name = db.Column(db.Text)
    Name = db.Column(db.Text, unique=True)

    # 장비 분류
    Category = db.Column(db.Text)
    Type = db.Column(db.Text)
    Item = db.Column(db.Text)

    # 상세 스펙
    Model_Number = db.Column(db.Text)
    Version_Number = db.Column(db.Text)
    Manufacturer_Name = db.Column(db.Text)
    Serial_Number = db.Column(db.Text)
    Description = db.Column(db.Text)
    Service_URL__c = db.Column(db.Text)
    IP_Address = db.Column(db.Text)
    Region = db.Column(db.Text)
    IDC_Site = db.Column(db.Text)

    # 상태 및 관리
    AssetLifecycleStatus = db.Column(db.Integer, default=0)
    Supported = db.Column(db.Integer, default=0)

    # 운영 정보
    Maintenance_Company = db.Column(db.Integer, default=0)
    Operation_Company = db.Column(db.Integer, default=0)
    Operation_Mode = db.Column(db.Integer, default=0)

    # 제품 정보
    Product_Name = db.Column(db.Text)
    Supplier = db.Column(db.Text)
    Owner = db.Column(db.Text)

    # 백업 설정
    C_backup = db.Column(db.Integer, default=1)
    C_cycle = db.Column(db.Integer)
    C_note = db.Column(db.Text)
    Short_Description = db.Column(db.Text)

    # 날짜 정보
    Receive_Date = db.Column(db.Date)
    PurchaseDate = db.Column(db.Date)
    InstallationDate = db.Column(db.Date)
    Available_Date = db.Column(db.Date)
    Disposal_Date = db.Column(db.Date)
    License_Expiry_Date = db.Column(db.Date)
    ReturnDate = db.Column(db.Date)
    LastScanDate = db.Column(db.Date, default=datetime.now)

    # Relationship
    people = db.relationship('CTMPeople', backref='assets', lazy=True)

    TYPE_ABBREVIATION_MAP = {
        'FW': ['방화벽', 'firewall', 'f/w', 'ngfw'],
        'SW': ['스위치', 'switch', 'l4', 'l3', 'backbone'],
        'RT': ['라우터', 'router'],
        'SV': ['서버', 'server'],
        'WAF': ['웹방화벽', 'waf', 'web firewall'],
        'IPS': ['ips', '침입방지'],
        'IDS': ['ids'],
        'DDOS': ['ddos', '디도스'],
        'UTM': ['utm'],
        'VPN': ['vpn'],
        'AP': ['ap', 'access point']
    }

    def get_type_abbreviation(self, type_text):
        if not type_text:
            return 'UNKNOWN'

        type_lower = type_text.lower()
        for abbr, keywords in self.TYPE_ABBREVIATION_MAP.items():
            if any(keyword in type_lower for keyword in keywords):
                return abbr

        return type_text.replace(' ', '_').upper()

    def generate_unique_name(self):
        if not self.Owner_name or not self.Type:
            return None

        type_abbr = self.get_type_abbreviation(self.Type)
        base_name = f"{self.Owner_name}_{type_abbr}"

        existing = db.session.query(AST_Computer_System).filter(
            AST_Computer_System.Name.like(f"{base_name}_%")
        ).all()

        if not existing:
            return f"{base_name}_1"

        max_index = 0
        pattern = re.compile(rf"^{re.escape(base_name)}_(\d+)$")

        for asset in existing:
            if asset.Name:
                match = pattern.match(asset.Name)
                if match:
                    index = int(match.group(1))
                    max_index = max(max_index, index)

        return f"{base_name}_{max_index + 1}"

    def save(self):
        if not self.Name:
            self.Name = self.generate_unique_name()

        self.LastScanDate = datetime.now().date()
        db.session.add(self)
        db.session.commit()


@event.listens_for(AST_Computer_System, 'before_insert')
def receive_before_insert(mapper, connection, target):
    if not target.Name and target.Owner_name and target.Type:
        target.Name = target.generate_unique_name()