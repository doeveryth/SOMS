from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import datetime
import uuid

from ..extensions import db
from ..models.ctm_people import CTMPeople
from ..models.customer_notes import CustomerNote
from ..models.work_info import WorkInfo
from ..models.ast_computersystem import AST_Computer_System
from ..models.servers import ServerInfo
from ..models.contacts import Contact
from ..models.contracts import Contract

bp = Blueprint("customers", __name__, url_prefix="/customers")


SEVERITIES = ["P1", "P2", "P3"]
DEFAULT_TAGS = [
    "보안", "접속/계정", "백업", "모니터링", "장비(CI)", "계약",
    "유지보수", "작업이력", "장애이력", "고객요청", "운영주의", "기타",
]

# ... existing code ...


@bp.post("/<person_id>/ci")
@login_required
def add_ci(person_id: str):
    name = (request.form.get("Name") or "").strip()
    if not name:
        flash("CI 장비명은 필수입니다.", "danger")
        return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))

    item = AST_Computer_System(
        Name=name,
        Person_ID=person_id,
        Model_Number=request.form.get("Model_Number") or None,
        AssetLifecycleStatus=request.form.get("AssetLifecycleStatus") or None,
        Short_Description=request.form.get("Short_Description") or '',
    )
    db.session.add(item)
    db.session.commit()
    flash("보안장비가 추가되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))


@bp.post("/<person_id>/servers")
@login_required
def add_server(person_id: str):
    item = ServerInfo(
        Person_ID=person_id,
        chServerName=request.form.get("chServerName") or None,
        chServerInfo=request.form.get("chServerInfo") or None,
        Submitter=current_user.user_id,
        Create_Date=datetime.utcnow(),
    )
    db.session.add(item)
    db.session.commit()
    flash("서버가 추가되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))


def _parse_date(value: str | None):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@bp.route("", methods=["GET", "POST"])
@login_required
def list_customers():
    if request.method == "POST":
        company = request.form.get("Company", "").strip()
        if not company:
            flash("고객명은 필수입니다.", "danger")
            return redirect(url_for("customers.list_customers"))

        person_id = f"P-{uuid.uuid4().hex[:12]}"

        people = CTMPeople(
            Person_ID=person_id,
            Company=company,
            Last_Name=request.form.get("Last_Name") or None,
            Service_Type=request.form.get("Service_Type") or None,
            Client_Type=request.form.get("Client_Type") or None,
            Open_Date=_parse_date(request.form.get("Open_Date")),
            Terminate_Date=_parse_date(request.form.get("Terminate_Date")),
            chHistory=request.form.get("chHistory") or None,
            chEtc=request.form.get("chEtc") or None,
            Sales_Manager=request.form.get("Sales_Manager") or None,
            contract_memo__c=request.form.get("contract_memo__c") or None,
            Service_Contract_Amount__c=request.form.get("Service_Contract_Amount__c") or None,
            Service_Status=request.form.get("Service_Status") or None,
            IDC=request.form.get("IDC") or None,
            Rack_Location=request.form.get("Rack_Location") or None,
            Client_Sensitivity=request.form.get("Client_Sensitivity") or None,
            Report_YN=request.form.get("Report_YN") or None,
            Customer_Folder=request.form.get("Customer_Folder") or None,
            Customer_Folder_Detail=request.form.get("Customer_Folder_Detail") or None,
            Service_URL__c=request.form.get("Service_URL__c") or None,
            Business_Type=request.form.get("Business_Type") or None,
            Business_Detail=request.form.get("Business_Detail") or None,
            Backup_Service=request.form.get("Backup_Service") or None,
            Backup_Type=request.form.get("Backup_Type") or None,
            Backup_Period=request.form.get("Backup_Period") or None,
            Backup_Path=request.form.get("Backup_Path") or None,

            Vaccine__c=request.form.get("Vaccine__c") or None,
            ShellMonitor__c=request.form.get("ShellMonitor__c") or None,

            Other_Info=request.form.get("Other_Info") or None,
        )

        db.session.add(people)
        db.session.commit()
        flash("고객이 등록되었습니다.", "success")
        return redirect(url_for("customers.detail", person_id=people.Person_ID))

    q = request.args.get("q", "").strip()

    query = db.session.query(CTMPeople)
    if q:
        query = query.filter(or_(CTMPeople.Company.ilike(f"%{q}%"), CTMPeople.Last_Name.ilike(f"%{q}%")))

    people = query.order_by(CTMPeople.Company.asc().nulls_last()).limit(200).all()
    return render_template("customers/list.html", people=people, q=q)


def _split_handler(detail: str | None):
    if not detail:
        return "", ""
    prefix = "[처리자:"
    if detail.startswith(prefix) and "]" in detail:
        end = detail.find("]")
        handler = detail[len(prefix):end].strip()
        rest = detail[end + 1 :]
        if rest.startswith("\n"):
            rest = rest[1:]
        return handler, rest
    return "", detail or ""


@bp.get("/<person_id>")
@login_required
def detail(person_id: str):
    people = (
        db.session.query(CTMPeople)
        .filter(CTMPeople.Person_ID == person_id)
        .first()
    )
    if not people:
        flash("고객을 찾을 수 없습니다.", "warning")
        return redirect(url_for("customers.list_customers"))

    notes = (
        db.session.query(CustomerNote)
        .filter(CustomerNote.Person_ID == person_id)
        .filter(CustomerNote.Deleted_YN == "N")
        .order_by(CustomerNote.Created_At.desc())
        .limit(50)
        .all()
    )

    work_rows = (
        db.session.query(WorkInfo)
        .filter(WorkInfo.Person_ID == person_id)
        .order_by(WorkInfo.Work_Date.desc().nulls_last(), WorkInfo.Work_ID.desc())
        .limit(200)
        .all()
    )

    ci_rows = (
        db.session.query(AST_Computer_System)
        .filter(AST_Computer_System.Person_ID == person_id)
        .order_by(AST_Computer_System.Name.asc())
        .limit(200)
        .all()
    )

    server_rows = (
        db.session.query(ServerInfo)
        .filter(ServerInfo.Person_ID == person_id)
        .order_by(ServerInfo.Server_ID.desc())
        .limit(200)
        .all()
    )

    contact_rows = (
        db.session.query(Contact)
        .filter(Contact.Person_ID == person_id)
        .order_by(Contact.Contact_ID.desc())
        .limit(200)
        .all()
    )

    contract_rows = (
        db.session.query(Contract)
        .filter(Contract.Person_ID == person_id)
        .filter(Contract.Deleted_YN == "N")
        .order_by(Contract.Contract_ID.desc())
        .limit(200)
        .all()
    )

    return render_template(
        "customers/detail.html",
        people=people,
        notes=notes,
        severities=SEVERITIES,
        tags=DEFAULT_TAGS,
        work_rows=work_rows,
        split_handler=_split_handler,
        ci_rows=ci_rows,
        server_rows=server_rows,
        contact_rows=contact_rows,
        contract_rows=contract_rows,
    )


@bp.post("/<person_id>/edit")
@login_required
def update_customer(person_id: str):
    people = (
        db.session.query(CTMPeople)
        .filter(CTMPeople.Person_ID == person_id)
        .first()
    )
    if not people:
        flash("고객을 찾을 수 없습니다.", "warning")
        return redirect(url_for("customers.list_customers"))

    company = request.form.get("Company", "").strip()
    if not company:
        flash("고객명은 필수입니다.", "danger")
        return redirect(url_for("customers.detail", person_id=person_id))

    people.Company = company
    people.Last_Name = request.form.get("Last_Name") or None
    people.Service_Type = request.form.get("Service_Type") or None
    people.Client_Type = request.form.get("Client_Type") or None
    people.Open_Date = _parse_date(request.form.get("Open_Date"))
    people.Terminate_Date = _parse_date(request.form.get("Terminate_Date"))
    people.chHistory = request.form.get("chHistory") or None
    people.chEtc = request.form.get("chEtc") or None
    people.Sales_Manager = request.form.get("Sales_Manager") or None
    people.contract_memo__c = request.form.get("contract_memo__c") or None
    people.Service_Contract_Amount__c = request.form.get("Service_Contract_Amount__c") or None
    db.session.commit()
    flash("고객 정보가 수정되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id))


@bp.post("/<person_id>/contacts")
@login_required
def add_contact(person_id: str):
    contact = Contact(
        Person_ID=person_id,
        Role_Type=request.form.get("Role_Type") or None,
        Name=request.form.get("Name") or None,
        Phone=request.form.get("Phone") or None,
        Email=request.form.get("Email") or None,
        Status=request.form.get("Status") or None,
        SMS_Receive_YN=request.form.get("SMS_Receive_YN") or None,
        Report_Receive_YN=request.form.get("Report_Receive_YN") or None,
    )
    db.session.add(contact)
    db.session.commit()
    flash("담당자가 추가되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-admin"))


@bp.post("/<person_id>/contracts")
@login_required
def add_contract(person_id: str):
    contract = Contract(
        Person_ID=person_id,
        Contract_Name=request.form.get("Contract_Name") or None,
        Contract_Amount=request.form.get("Contract_Amount") or None,
        Currency=request.form.get("Currency") or None,
        Contract_Start_Date=_parse_date(request.form.get("Contract_Start_Date")),
        Contract_End_Date=_parse_date(request.form.get("Contract_End_Date")),
        Contract_Notes=request.form.get("Contract_Notes") or None,
        Submitter=current_user.user_id,
        Create_Date=datetime.utcnow(),
        Deleted_YN="N",
    )
    db.session.add(contract)
    db.session.commit()
    flash("계약이 추가되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-admin"))


@bp.post("/<person_id>/ci/<int:asset_id>/delete")
@login_required
def delete_ci(person_id: str, asset_id: int):
    item = db.session.get(AST_Computer_System , asset_id)
    if not item or item.Person_ID != person_id:
        flash("보안장비를 찾을 수 없습니다.", "warning")
        return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))

    db.session.delete(item)
    db.session.commit()
    flash("보안장비가 삭제되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))


@bp.post("/<person_id>/servers/<int:server_id>/delete")
@login_required
def delete_server(person_id: str, server_id: int):
    item = db.session.get(ServerInfo, server_id)
    if not item or item.Person_ID != person_id:
        flash("서버를 찾을 수 없습니다.", "warning")
        return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))

    db.session.delete(item)
    db.session.commit()
    flash("서버가 삭제되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))


@bp.post("/<person_id>/contacts/<int:contact_id>/delete")
@login_required
def delete_contact(person_id: str, contact_id: int):
    item = db.session.get(Contact, contact_id)
    if not item or item.Person_ID != person_id:
        flash("담당자를 찾을 수 없습니다.", "warning")
        return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-admin"))

    db.session.delete(item)
    db.session.commit()
    flash("담당자가 삭제되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-admin"))


@bp.post("/<person_id>/contracts/<int:contract_id>/delete")
@login_required
def delete_contract(person_id: str, contract_id: int):
    item = db.session.get(Contract, contract_id)
    if not item or item.Person_ID != person_id:
        flash("계약을 찾을 수 없습니다.", "warning")
        return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-admin"))

    item.Deleted_YN = "Y"
    item.Deleted_At = datetime.utcnow()
    db.session.commit()
    flash("계약이 삭제(숨김)되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-admin"))


@bp.get('/<person_id>/assets')
@login_required
def view_assets(person_id):
    """보안장비 목록 조회"""
    people = db.session.query(CTMPeople).filter(CTMPeople.Person_ID == person_id).first_or_404()
    assets = db.session.query(AST_Computer_System).filter(AST_Computer_System.Person_ID == person_id).all()
    return render_template('customers/assets.html', people=people, assets=assets)


@bp.route('/<person_id>/assets/add', methods=['GET', 'POST'])
@login_required
def add_asset(person_id):
    """보안장비 등록"""
    people = db.session.query(CTMPeople).filter(CTMPeople.Person_ID == person_id).first_or_404()

    if request.method == 'POST':
        # Type을 약어로 변환
        type_input = request.form.get('type', '').strip()
        type_abbr = convert_type_to_abbreviation(type_input)

        # Owner_name 자동 설정
        owner_name = people.Last_Name or people.Company

        # CI 이름 자동 생성 (중복 방지)
        ci_name = generate_unique_ci_name(owner_name, type_abbr)

        asset = AST_Computer_System(
            Person_ID=person_id,
            Company=people.Company,
            Owner_name=owner_name,
            Name=ci_name,  # 자동 생성된 이름
            Category=request.form.get('category'),
            Type=type_input,
            Item=request.form.get('item'),
            Model_Number=request.form.get('model_number'),
            Version_Number=request.form.get('version_number'),
            Manufacturer_Name=request.form.get('manufacturer_name'),
            Serial_Number=request.form.get('serial_number'),
            Description=request.form.get('description'),
            Service_URL__c=request.form.get('service_url'),
            AssetLifecycleStatus=int(request.form.get('lifecycle_status', 3)),
            Supported=int(request.form.get('supported', 0)),
            C_backup=int(request.form.get('c_backup', 0)),
            C_cycle=int(request.form.get('c_cycle')) if request.form.get('c_cycle') else None,
            C_note=request.form.get('cfg_note'),
            Short_Description=request.form.get('ci_note'),
            IP_Address=request.form.get('ip_info'),
            Region=request.form.get('region'),
            IDC_Site=request.form.get('idc_site'),
            Maintenance_Company=int(request.form.get('maintenance_company', 0)),
            Operation_Company=int(request.form.get('operation_company', 0)),
            Operation_Mode=int(request.form.get('operation_mode', 0)),
            Product_Name=request.form.get('product_name'),
            Supplier=request.form.get('supplier'),
            Owner=request.form.get('owner')
        )

        # 날짜 필드 처리
        date_fields = {
            'installation_date': 'InstallationDate',
            'disposal_date': 'Disposal_Date',
            'license_expiry': 'License_Expiry_Date'
        }
        for field, attr in date_fields.items():
            date_str = request.form.get(field)
            if date_str:
                try:
                    setattr(asset, attr, datetime.strptime(date_str, '%Y-%m-%d').date())
                except ValueError:
                    pass

        asset.save()
        flash(f'보안장비가 등록되었습니다. (CI 이름: {ci_name})', 'success')
        return redirect(url_for('customers.detail', person_id=person_id, _anchor='tab-assets'))

    return render_template('customers/detail.html', people=people)


def convert_type_to_abbreviation(type_input):
    """장비 유형을 약어로 변환"""
    type_lower = type_input.lower()

    type_map = {
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

    for abbr, keywords in type_map.items():
        if any(keyword in type_lower for keyword in keywords):
            return abbr

    return type_input.upper().replace(' ', '_')


def generate_unique_ci_name(owner_name, type_abbr):
    """중복되지 않는 CI 이름 생성"""
    base_name = f"{owner_name}_{type_abbr}"

    # 같은 패턴으로 시작하는 모든 장비 조회
    existing_assets = db.session.query(AST_Computer_System).filter(
        AST_Computer_System.Name.like(f"{base_name}_%")
    ).all()

    if not existing_assets:
        return f"{base_name}_1"

    # 기존 인덱스 추출
    existing_indices = []
    for asset in existing_assets:
        try:
            parts = asset.Name.split('_')
            if parts[-1].isdigit():
                existing_indices.append(int(parts[-1]))
        except (IndexError, ValueError):
            continue

    # 다음 인덱스 계산
    next_index = max(existing_indices) + 1 if existing_indices else 1
    return f"{base_name}_{next_index}"
