from app import db
from datetime import datetime


class AST_Computer_System(db.Model):
    __tablename__ = 'AST_Computer_System'
    __table_args__ = {'extend_existing': True}

    # ----------------------------------------------------------------
    # [1] 기본 식별 및 참조
    # ----------------------------------------------------------------
    Asset_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Person_ID = db.Column(db.Text, db.ForeignKey('CTM_People.Person_ID'), nullable=False)

    Company = db.Column(db.Text)  # 고객사명
    Owner_name = db.Column(db.Text)  # ★ 사이트명으로 사용 (서울 본사, 부산 지사 등)
    Name = db.Column(db.Text, unique=True)  # CI 이름 (Hostname) - 사용자 직접 입력

    # ----------------------------------------------------------------
    # [2] 장비 분류
    # ----------------------------------------------------------------
    Category = db.Column(db.Text)  # 계층 1 (보안장비)
    Type = db.Column(db.Text)  # 계층 2 (방화벽, 스위치 등)
    Item = db.Column(db.Text)  # 계층 3 (Fortinet, Ahnlab 등)

    # ----------------------------------------------------------------
    # [3] 상세 스펙
    # ----------------------------------------------------------------
    Model_Number = db.Column(db.Text)  # 모델명
    Version_Number = db.Column(db.Text)  # 버전
    Manufacturer_Name = db.Column(db.Text)  # 제조사
    Serial_Number = db.Column(db.Text)  # 시리얼 번호
    Description = db.Column(db.Text)  # 비고
    Service_URL__c = db.Column(db.Text)  # 서비스 URL
    IP_Address = db.Column(db.Text)  # IP 주소
    Region = db.Column(db.Text)  # 리전 (필요시)
    IDC_Site = db.Column(db.Text)  # DC 위치

    # ----------------------------------------------------------------
    # [4] 상태 및 관리
    # ----------------------------------------------------------------
    AssetLifecycleStatus = db.Column(db.Integer, default=0)  # 상태 (사용중, 폐기 등)
    Supported = db.Column(db.Integer, default=0)  # 기술지원 여부

    # ----------------------------------------------------------------
    # [5] 운영 정보
    # ----------------------------------------------------------------
    Maintenance_Company = db.Column(db.Integer, default=0)  # 유지보수 업체 코드
    Operation_Company = db.Column(db.Integer, default=0)  # 운영 업체 코드
    Operation_Mode = db.Column(db.Integer, default=0)  # 운영 모드 (탐지/차단)

    # ----------------------------------------------------------------
    # [6] 제품 정보
    # ----------------------------------------------------------------
    Product_Name = db.Column(db.Text)  # 제품명
    Supplier = db.Column(db.Text)  # 공급자 (임대, 고객소유 등)
    Owner = db.Column(db.Text)  # 소유자 (필요시 사용)

    # ----------------------------------------------------------------
    # [7] 백업 설정
    # ----------------------------------------------------------------
    C_backup = db.Column(db.Integer, default=1)  # 백업 여부
    C_cycle = db.Column(db.Integer)  # 백업 주기
    C_note = db.Column(db.Text)  # 백업 특이사항
    Short_Description = db.Column(db.Text)  # 장비 특이사항 (요약)

    # ----------------------------------------------------------------
    # [8] 날짜 정보
    # ----------------------------------------------------------------
    Receive_Date = db.Column(db.Date)  # 입고일
    PurchaseDate = db.Column(db.Date)  # 구매일
    InstallationDate = db.Column(db.Date)  # 설치일
    Available_Date = db.Column(db.Date)  # 가용일
    Disposal_Date = db.Column(db.Date)  # 폐기일
    License_Expiry_Date = db.Column(db.Date)  # 라이선스 만료일
    ReturnDate = db.Column(db.Date)  # 반환일
    LastScanDate = db.Column(db.Date, default=datetime.now)

    # ----------------------------------------------------------------
    # [9] 메타 데이터
    # ----------------------------------------------------------------
    Submitter = db.Column(db.Text)  # 등록자
    Update_Date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 수정일

    # Relationship
    people = db.relationship('CTMPeople', backref='assets', lazy=True)