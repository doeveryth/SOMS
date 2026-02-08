import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import datetime
import uuid
import json


from ..extensions import db
from ..models.ctm_people import CTMPeople
from ..models.customer_notes import CustomerNote
from ..models.work_info import WorkInfo
from ..models.ast_computersystem import AST_Computer_System
from ..models.servers import ServerInfo
from ..models.contacts import Contact
from ..models.contracts import Contract
from ..models.work_attachments import WorkAttachment

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


def _parse_date(value: str | None):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@bp.route("", methods=["GET", "POST"])
@login_required
def list_customers():
    # [POST] 고객 등록 로직 (기존과 동일)
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
            Open_Date=_parse_date(request.form.get("Open_Date")),
            Terminate_Date=_parse_date(request.form.get("Terminate_Date")),
            Service_Number=request.form.get("Service_Number") or None,
            Service_Status=request.form.get("Service_Status") or None,
            IDC=request.form.get("IDC") or None,
            Rack_Location=request.form.get("Rack_Location") or None,
            Client_Sensitivity=request.form.get("Client_Sensitivity") or None,
            Report_YN=request.form.get("Report_YN") or None,
            Sales_Manager=request.form.get("Sales_Manager") or None,
        )

        db.session.add(people)
        db.session.commit()
        flash("고객이 등록되었습니다.", "success")
        return redirect(url_for("customers.detail", person_id=people.Person_ID))

    # [GET] 조회 및 필터링 로직 (여기 수정됨)
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    sensitivity = request.args.get("sensitivity", "").strip()

    query = db.session.query(CTMPeople)

    # 1. 텍스트 검색 (이름, 사이트, 번호, DC, 유형)
    if q:
        query = query.filter(
            or_(
                CTMPeople.Company.ilike(f"%{q}%"),
                CTMPeople.Last_Name.ilike(f"%{q}%"),
                CTMPeople.Service_Number.ilike(f"%{q}%"),
                CTMPeople.IDC.ilike(f"%{q}%"),
                CTMPeople.Service_Type.ilike(f"%{q}%"),
            )
        )

    # 2. 상태 필터 (Dropdown) - AND 조건
    if status:
        query = query.filter(CTMPeople.Service_Status == status)

    # 3. 민감도 필터 (Dropdown) - AND 조건
    if sensitivity:
        query = query.filter(CTMPeople.Client_Sensitivity == sensitivity)

    people = query.order_by(CTMPeople.Company.asc().nulls_last()).limit(200).all()

    # 템플릿에 필터 상태(q, status, sensitivity)를 다시 전달하여 유지시킴
    return render_template("customers/list.html", people=people, q=q, status=status, sensitivity=sensitivity)

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


# [고객 정보 수정 - AJAX 방식]
@bp.post("/<person_id>/update")  # 1. 자바스크립트 경로와 일치시킴 (/edit -> /update)
@login_required
def update_customer_info(person_id: str):
    # 1. DB에서 사용자 조회
    people = db.session.query(CTMPeople).filter(CTMPeople.Person_ID == person_id).first()

    if not people:
        # 2. 에러 시 JSON 반환
        return jsonify({"ok": False, "message": "고객을 찾을 수 없습니다."}), 404

    try:
        # 3. 데이터 매핑 (기존 로직 유지)
        people.Company = request.form.get("company", "").strip()
        people.Last_Name = request.form.get("last_name") or None
        people.Service_Type = request.form.get("service_type") or None
        people.Service_Status = request.form.get("profile_status") or None

        people.Business_Type = request.form.get("industry_category") or None
        people.Business_Detail = request.form.get("industry_detail") or None

        people.Client_Sensitivity = request.form.get("client_sensitivity") or None
        people.Report_YN = request.form.get("report_yn") or None

        people.Service_URL__c = request.form.get("service_url") or None
        people.Service_Number = request.form.get("service_number") or None
        people.Customer_Folder = request.form.get("customer_folder") or None

        people.Open_Date = _parse_date(request.form.get("open_date"))
        people.Terminate_Date = _parse_date(request.form.get("close_date"))

        people.IDC = request.form.get("dc_location") or None
        people.Rack_Location = request.form.get("rack_location") or None

        # [4. 중요!] 신규 추가된 계약 관련 필드 매핑
        people.Contract_Amount = request.form.get("contract_amount") or None
        people.Contract_Note = request.form.get("contract_note") or None

        # 백업 정보
        people.Backup_Service = request.form.get("backup_service_yn") or None
        people.Backup_Type = request.form.get("backup_type") or None
        people.Backup_Period = request.form.get("backup_period_volume") or None
        people.Backup_Path = request.form.get("backup_path") or None

        # 보안 솔루션
        people.Vaccine__c = request.form.get("vaccine_yn") or None
        people.ShellMonitor__c = request.form.get("shell_monitor_yn") or None

        # 메모 및 특이사항
        people.chHistory = request.form.get("intrusion_notes") or None
        people.chEtc = request.form.get("customer_notes") or None

        db.session.commit()

        # 5. 성공 시 JSON 반환 (SweetAlert가 이걸 받아서 처리함)
        return jsonify({"ok": True, "message": "고객 정보가 수정되었습니다."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": f"수정 중 오류 발생: {str(e)}"}), 500


# 날짜 변환 헬퍼 함수 (필요한 경우 함수 밖이나 위에 정의)
def _parse_date(date_str):
    if not date_str: return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

# [1] 담당자 추가 (JSON 반환)
@bp.post("/<person_id>/contacts/add")
@login_required
def add_contact(person_id):
    try:
        new_contact = Contact(
            Person_ID=person_id,
            Role_Type=request.form.get('role_type'),
            Name=request.form.get('name'),
            General_Phone=request.form.get('general_phone'),
            Phone=request.form.get('phone'),
            Email=request.form.get('email'),
            Status=request.form.get('status', '활성화'),
            SMS_Receive_YN=request.form.get('sms_yn', 'N'),
            Report_Receive_YN=request.form.get('report_yn', 'N'),
            Reg_Date=datetime.now()
        )
        db.session.add(new_contact)
        db.session.commit()
        return jsonify({"ok": True, "message": "담당자가 등록되었습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


# [2] 담당자 조회 (수정 팝업용)
@bp.get("/<person_id>/contacts/<int:contact_id>/edit")
@login_required
def get_contact_info(person_id, contact_id):
    c = db.session.get(Contact, contact_id)
    if not c:
        return jsonify({"ok": False, "message": "데이터 없음"}), 404

    return jsonify({
        "ok": True,
        "data": {
            "id": c.Contact_ID,
            "role": c.Role_Type,
            "name": c.Name,
            "gen_phone": c.General_Phone,
            "phone": c.Phone,
            "email": c.Email,
            "status": c.Status,
            "sms_yn": c.SMS_Receive_YN,
            "report_yn": c.Report_Receive_YN
        }
    })


# [3] 담당자 수정 (JSON 반환)
@bp.post("/<person_id>/contacts/<int:contact_id>/edit")
@login_required
def update_contact(person_id, contact_id):
    try:
        c = db.session.get(Contact, contact_id)
        if not c:
            return jsonify({"ok": False, "message": "데이터 없음"}), 404

        c.Role_Type = request.form.get('role_type')
        c.Name = request.form.get('name')
        c.General_Phone = request.form.get('general_phone')
        c.Phone = request.form.get('phone')
        c.Email = request.form.get('email')
        c.Status = request.form.get('status')
        c.SMS_Receive_YN = request.form.get('sms_yn')
        c.Report_Receive_YN = request.form.get('report_yn')

        db.session.commit()
        # [핵심] 메시지를 JSON으로 보냄
        return jsonify({"ok": True, "message": "담당자 정보가 수정되었습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500

# [4] 담당자 삭제 (JSON 반환)
@bp.post("/<person_id>/contacts/<int:contact_id>/delete")
@login_required
def delete_contact(person_id, contact_id):
    try:
        c = db.session.get(Contact, contact_id)
        if not c:
            return jsonify({"ok": False, "message": "데이터 없음"}), 404

        db.session.delete(c)
        db.session.commit()
        return jsonify({"ok": True, "message": "삭제되었습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


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
        # 1. 사용자 입력 장비명 가져오기
        input_ci_name = request.form.get('ci_name', '').strip()

        # Owner_name 자동 설정 (회사명 우선)
        owner_name = people.Last_Name or people.Company

        if input_ci_name:
            # 사용자가 입력한 경우 그대로 사용
            ci_name = input_ci_name
        else:
            # 2. 입력이 없을 경우 기존 자동 생성 로직 (Fallback)
            type_input = request.form.get('type', '').strip()
            type_abbr = convert_type_to_abbreviation(type_input)
            ci_name = generate_unique_ci_name(owner_name, type_abbr)

        # DB 모델 생성
        asset = AST_Computer_System(
            Person_ID=person_id,
            Company=people.Company,
            Owner_name=owner_name,

            # [수정됨] 결정된 CI 이름 저장
            Name=ci_name,

            # 기본 장비 정보
            Category=request.form.get('category'),
            Type=request.form.get('type'),
            Item=request.form.get('item'),

            # 하드웨어 스펙
            Product_Name=request.form.get('product_name'),
            Model_Number=request.form.get('model_number'),
            Manufacturer_Name=request.form.get('manufacturer_name'),

            # 식별 정보
            Serial_Number=request.form.get('serial_number'),
            IP_Address=request.form.get('ip_info'),  # HTML name='ip_info' 매핑

            # 운영 정보
            Supplier=request.form.get('supplier'),
            Maintenance_Company=int(request.form.get('maintenance_company', 0)),
            Operation_Company=int(request.form.get('operation_company', 0)),
            Operation_Mode=int(request.form.get('operation_mode', 0)),
            IDC_Site=request.form.get('idc_site'),

            # 백업 설정
            C_backup=int(request.form.get('c_backup', 0)),
            C_cycle=int(request.form.get('c_cycle')) if request.form.get('c_cycle') else None,
            C_note=request.form.get('cfg_note'),

            # 기타 및 상태
            Short_Description=request.form.get('ci_note'),  # 장비 특이사항
            Description=request.form.get('description'),  # 비고
            AssetLifecycleStatus=int(request.form.get('lifecycle_status', 3)),

            # 아래 필드들은 폼에 없으면 None 혹은 기본값 처리
            Version_Number=request.form.get('version_number'),
            Service_URL__c=request.form.get('service_url'),
            Supported=int(request.form.get('supported', 0)),
            Region=request.form.get('region'),
            Owner=request.form.get('owner'),

            Submitter = current_user.user_name if hasattr(current_user, 'user_name') else 'Unknown',
            Update_Date = datetime.now(),
        )

        # 날짜 필드 처리 (빈 문자열 에러 방지)
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
                    pass  # 날짜 형식이 잘못된 경우 무시 (혹은 로깅)

        try:
            db.session.add(asset)  # asset.save() 대신 session.add 권장 (SQLAlchemy 버전에 따라 다름)
            db.session.commit()
            flash(f'보안장비가 등록되었습니다. (장비명: {ci_name})', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'장비 등록 중 오류가 발생했습니다: {str(e)}', 'danger')

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


@bp.get("/<person_id>/ci/<int:asset_id>/edit")
@login_required
def edit_ci_form(person_id: str, asset_id: int):
    """보안장비 수정 폼 로드"""
    item = db.session.get(AST_Computer_System, asset_id)
    if not item or item.Person_ID != person_id:
        return {"ok": False, "message": "보안장비를 찾을 수 없습니다."}, 404

    return {
        "ok": True,
        "data": {
            "asset_id": item.Asset_ID,
            "name": item.Name,
            "category": item.Category,
            "type": item.Type,
            "item": item.Item,
            "model_number": item.Model_Number,
            "version_number": item.Version_Number,
            "manufacturer_name": item.Manufacturer_Name,
            "serial_number": item.Serial_Number,
            "description": item.Description,
            "service_url": item.Service_URL__c,
            "lifecycle_status": item.AssetLifecycleStatus,
            "supported": item.Supported,
            "c_backup": item.C_backup,
            "c_cycle": item.C_cycle,
            "cfg_note": item.C_note,
            "ci_note": item.Short_Description,
            "ip_info": item.IP_Address,
            "region": item.Region,
            "idc_site": item.IDC_Site,
            "maintenance_company": item.Maintenance_Company,
            "operation_company": item.Operation_Company,
            "operation_mode": item.Operation_Mode,
            "product_name": item.Product_Name,
            "supplier": item.Supplier,
            "owner": item.Owner,
            "installation_date": item.InstallationDate.isoformat() if item.InstallationDate else "",
            "disposal_date": item.Disposal_Date.isoformat() if item.Disposal_Date else "",
            "license_expiry": item.License_Expiry_Date.isoformat() if item.License_Expiry_Date else "",
        }
    }


@bp.post("/<person_id>/ci/<int:asset_id>/edit")
@login_required
def update_ci(person_id: str, asset_id: int):
    """보안장비 수정"""
    item = db.session.get(AST_Computer_System, asset_id)
    if not item or item.Person_ID != person_id:
        flash("보안장비를 찾을 수 없습니다.", "warning")
        return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))

    # [수정] CI 이름(장비 식별명) 업데이트 추가
    item.Name = request.form.get('ci_name')

    item.Category = request.form.get('category')
    item.Type = request.form.get('type')
    item.Item = request.form.get('item')
    item.Model_Number = request.form.get('model_number')
    item.Version_Number = request.form.get('version_number')
    item.Manufacturer_Name = request.form.get('manufacturer_name')
    item.Serial_Number = request.form.get('serial_number')
    item.Description = request.form.get('description')
    item.Service_URL__c = request.form.get('service_url')
    item.AssetLifecycleStatus = int(request.form.get('lifecycle_status', 3))
    item.Supported = int(request.form.get('supported', 0))
    item.C_backup = int(request.form.get('c_backup', 0))
    item.C_cycle = int(request.form.get('c_cycle')) if request.form.get('c_cycle') else None
    item.C_note = request.form.get('cfg_note')
    item.Short_Description = request.form.get('ci_note')
    item.IP_Address = request.form.get('ip_info')
    item.Region = request.form.get('region')
    item.IDC_Site = request.form.get('idc_site')
    item.Maintenance_Company = int(request.form.get('maintenance_company', 0))
    item.Operation_Company = int(request.form.get('operation_company', 0))
    item.Operation_Mode = int(request.form.get('operation_mode', 0))
    item.Product_Name = request.form.get('product_name')
    item.Supplier = request.form.get('supplier')
    item.Owner = request.form.get('owner')
    item.Update_Date = datetime.now()

    date_fields = {
        'installation_date': 'InstallationDate',
        'disposal_date': 'Disposal_Date',
        'license_expiry': 'License_Expiry_Date'
    }
    for field, attr in date_fields.items():
        date_str = request.form.get(field)
        if date_str:
            try:
                setattr(item, attr, datetime.strptime(date_str, '%Y-%m-%d').date())
            except ValueError:
                pass
        else:
            # 날짜를 지우고 싶을 경우를 대비해 None 처리 (선택사항)
            setattr(item, attr, None)

    db.session.commit()
    flash("보안장비가 수정되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-assets"))


# [1] 서버 추가 (일괄 등록 - JSON 반환)
@bp.post("/<person_id>/servers/add")  # URL 주의: /server/add -> /servers/add 로 통일함
@login_required
def add_server(person_id):
    # form에서 배열로 값 가져오기
    names = request.form.getlist('server_names[]')
    ips = request.form.getlist('server_ips[]')

    if not names:
        return jsonify({"ok": False, "message": "입력된 서버 정보가 없습니다."}), 400

    try:
        count = 0
        # 이름과 IP를 짝지어 반복 (zip)
        for name, ip in zip(names, ips):
            if not name.strip(): continue  # 이름 없으면 패스

            # 등록자 이름 안전하게 가져오기
            submitter = getattr(current_user, 'user_name', getattr(current_user, 'name', 'System'))

            new_server = ServerInfo(
                Person_ID=person_id,
                chServerName=name,
                chServerInfo=ip,
                Submitter=submitter,
                Create_Date=datetime.now()
            )
            db.session.add(new_server)
            count += 1

        db.session.commit()
        return jsonify({"ok": True, "message": f"{count}대의 서버가 등록되었습니다."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


# [2] 서버 수정 폼 데이터 조회 (기존 유지)
@bp.get("/<person_id>/servers/<int:server_id>/edit")
@login_required
def get_server_info(person_id, server_id):
    server = db.session.get(ServerInfo, server_id)
    if not server:
        return jsonify({"ok": False, "message": "서버를 찾을 수 없습니다."}), 404

    return jsonify({
        "ok": True,
        "data": {
            "id": server.Server_ID,
            "server_name": server.chServerName,
            "server_ip": server.chServerInfo
        }
    })


# [3] 서버 수정 처리 (JSON 반환)
@bp.post("/<person_id>/servers/<int:server_id>/edit")
@login_required
def update_server(person_id, server_id):
    try:
        server = db.session.get(ServerInfo, server_id)
        if not server:
            return jsonify({"ok": False, "message": "데이터 없음"}), 404

        server.chServerName = request.form.get('server_name')
        server.chServerInfo = request.form.get('server_ip')

        db.session.commit()
        # [핵심] JSON으로 성공 메시지 반환
        return jsonify({"ok": True, "message": "서버 정보가 수정되었습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


# [4] 서버 삭제 (JSON 반환)
@bp.post("/<person_id>/servers/<int:server_id>/delete")
@login_required
def delete_server(person_id, server_id):
    try:
        server = db.session.get(ServerInfo, server_id)
        if not server:
            return jsonify({"ok": False, "message": "데이터 없음"}), 404

        db.session.delete(server)
        db.session.commit()
        # [핵심] JSON으로 성공 메시지 반환
        return jsonify({"ok": True, "message": "서버가 삭제되었습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500

@bp.get("/<person_id>/contacts/<int:contact_id>/edit")
@login_required
def edit_contact_form(person_id: str, contact_id: int):
    """담당자 수정 폼 로드"""
    item = db.session.get(Contact, contact_id)
    if not item or item.Person_ID != person_id:
        return {"ok": False, "message": "담당자를 찾을 수 없습니다."}, 404

    return {
        "ok": True,
        "data": {
            "contact_id": item.Contact_ID,
            "role_type": item.Role_Type,
            "name": item.Name,
            "phone": item.Phone,
            "email": item.Email,
            "status": item.Status,
            "sms_receive_yn": item.SMS_Receive_YN,
            "report_receive_yn": item.Report_Receive_YN,
        }
    }


@bp.get("/<person_id>/contracts/<int:contract_id>/edit")
@login_required
def edit_contract_form(person_id: str, contract_id: int):
    """계약 수정 폼 로드"""
    item = db.session.get(Contract, contract_id)
    if not item or item.Person_ID != person_id:
        return {"ok": False, "message": "계약을 찾을 수 없습니다."}, 404

    return {
        "ok": True,
        "data": {
            "contract_id": item.Contract_ID,
            "contract_name": item.Contract_Name,
            "contract_amount": item.Contract_Amount,
            "currency": item.Currency,
            "contract_start_date": item.Contract_Start_Date.isoformat() if item.Contract_Start_Date else "",
            "contract_end_date": item.Contract_End_Date.isoformat() if item.Contract_End_Date else "",
            "contract_notes": item.Contract_Notes,
        }
    }


@bp.post("/<person_id>/contracts/<int:contract_id>/edit")
@login_required
def update_contract(person_id: str, contract_id: int):
    """계약 수정"""
    item = db.session.get(Contract, contract_id)
    if not item or item.Person_ID != person_id:
        flash("계약을 찾을 수 없습니다.", "warning")
        return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-contracts"))

    item.Contract_Name = request.form.get('contract_name')
    item.Contract_Amount = request.form.get('contract_amount')
    item.Currency = request.form.get('currency')
    item.Contract_Start_Date = _parse_date(request.form.get('contract_start_date'))
    item.Contract_End_Date = _parse_date(request.form.get('contract_end_date'))
    item.Contract_Notes = request.form.get('contract_notes')
    db.session.commit()
    flash("계약이 수정되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=person_id, _anchor="tab-contracts"))


# [1] 작업 등록 (디버깅 강화 및 안전장치 추가)
@bp.post("/<person_id>/works/add")
@login_required
def add_work(person_id):
    try:
        print("=== [DEBUG] add_work Start ===")

        # 1. 요청 데이터 수신 확인 (여기서 에러나면 400 Bad Request)
        print(f"DEBUG: Form Keys: {list(request.form.keys())}")
        print(f"DEBUG: File Keys: {list(request.files.keys())}")

        # 2. 필수 데이터 검증
        work_date_str = request.form.get('work_date')
        work_type = request.form.get('work_type')

        print(f"DEBUG: work_date={work_date_str}, work_type={work_type}")

        if not work_date_str:
            return jsonify({"ok": False, "message": "작업일(Date)이 누락되었습니다."}), 400

        # 3. 등록자(Submitter) 이름 안전하게 가져오기 (User ID 오류 방지)
        # Flask-Login의 get_id() 메서드를 사용하는 것이 가장 안전합니다.
        try:
            if hasattr(current_user, 'user_name'):
                submitter = current_user.user_name
            elif hasattr(current_user, 'name'):
                submitter = current_user.name
            else:
                submitter = current_user.get_id() or "System"
        except Exception as e:
            print(f"DEBUG: User Attribute Error: {e}")
            submitter = "Unknown"

        submitter = str(submitter)
        print(f"DEBUG: Submitter={submitter}")

        # 4. DB 객체 생성
        new_work = WorkInfo(
            Person_ID=person_id,
            Work_Type=work_type,
            Work_Date=datetime.strptime(work_date_str, '%Y-%m-%d').date(),
            Summary=request.form.get('summary'),
            Description=request.form.get('description'),
            Submitter=submitter,
            Attachment_YN="N",
            Create_Date=datetime.now()
        )
        db.session.add(new_work)
        db.session.flush()

        # 5. 파일 처리
        files = request.files.getlist('files[]')

        # 만약 JS가 files로 보냈을 경우를 대비
        if not files:
            files = request.files.getlist('files')

        print(f"DEBUG: Files count: {len(files)}")

        has_file = False
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

        if not os.path.isabs(upload_folder):
            upload_folder = os.path.join(current_app.root_path, upload_folder)

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        for file in files:
            if file and file.filename.strip():
                has_file = True
                original_filename = file.filename

                # uuid import 확인
                import uuid
                ext = os.path.splitext(original_filename)[1]
                safe_filename = f"{new_work.Work_ID}_{uuid.uuid4().hex[:8]}{ext}"

                file_path = os.path.join(upload_folder, safe_filename)
                file.save(file_path)

                attachment = WorkAttachment(
                    Work_ID=new_work.Work_ID,
                    File_Name=original_filename,
                    File_Path=safe_filename,
                    File_Size=os.path.getsize(file_path),
                    Upload_Date=datetime.now()
                )
                db.session.add(attachment)

        if has_file:
            new_work.Attachment_YN = "Y"

        db.session.commit()
        print("=== [DEBUG] add_work Success ===")
        return jsonify({"ok": True, "message": "등록되었습니다."})

    except Exception as e:
        db.session.rollback()
        print(f"!!! CRITICAL ERROR !!!: {e}")
        import traceback
        traceback.print_exc()  # 상세 에러 로그 출력
        return jsonify({"ok": False, "message": f"서버 오류: {str(e)}"}), 500

# [2] 작업 수정 (파일 삭제 로직 복구 + 파일 추가)
@bp.post("/<person_id>/works/<int:work_id>/edit")
@login_required
def update_work(person_id, work_id):
    try:
        work = db.session.get(WorkInfo, work_id)
        if not work:
            return jsonify({"ok": False, "message": "해당 작업을 찾을 수 없습니다."}), 404

        # 1. 텍스트 정보 수정
        work.Work_Date = datetime.strptime(request.form.get('work_date'), '%Y-%m-%d').date()
        work.Work_Type = request.form.get('work_type')
        work.Summary = request.form.get('summary')
        work.Description = request.form.get('description')

        # 2. [복구됨] 파일 삭제 처리 (프론트엔드에서 보낸 delete_file_ids 처리)
        delete_ids_json = request.form.get('delete_file_ids')
        if delete_ids_json:
            try:
                delete_ids = json.loads(delete_ids_json)  # JSON 문자열 -> 리스트 변환
                if delete_ids:
                    attachments_to_delete = db.session.query(WorkAttachment).filter(
                        WorkAttachment.Work_ID == work_id,
                        WorkAttachment.Attachment_ID.in_(delete_ids)
                    ).all()

                    for att in attachments_to_delete:
                        # (선택사항) 실제 파일 삭제 로직이 필요하면 여기에 추가
                        # try:
                        #     os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], att.File_Path))
                        # except: pass
                        db.session.delete(att)
            except json.JSONDecodeError:
                pass

                # 3. 새 파일 추가
        files = request.files.getlist('files[]')
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        for file in files:
            if file and file.filename.strip():
                original_filename = file.filename
                ext = os.path.splitext(original_filename)[1]
                safe_filename = f"{work.Work_ID}_{uuid.uuid4().hex[:8]}{ext}"

                file_path = os.path.join(upload_folder, safe_filename)
                file.save(file_path)

                attachment = WorkAttachment(
                    Work_ID=work.Work_ID,
                    File_Name=original_filename,
                    File_Path=safe_filename,
                    File_Size=os.path.getsize(file_path),
                    Upload_Date=datetime.now()
                )
                db.session.add(attachment)

        # 4. Attachment_YN 상태 업데이트
        db.session.flush()
        count = db.session.query(WorkAttachment).filter_by(Work_ID=work_id).count()
        work.Attachment_YN = "Y" if count > 0 else "N"

        db.session.commit()
        return jsonify({"ok": True, "message": "수정되었습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


# [3] 파일 다운로드 (한글 이름으로 내보내기)
# 주의: 중복된 함수 중 경로 처리가 올바른 이 버전만 남김
@bp.route("/download/<int:attachment_id>")
def download_file(attachment_id):
    attachment = db.session.get(WorkAttachment, attachment_id)
    if not attachment:
        return "파일 정보를 찾을 수 없습니다.", 404

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    # DB에는 파일명만 저장되어 있으므로 폴더 경로와 합쳐야 함
    file_path = os.path.join(upload_folder, attachment.File_Path)

    if os.path.exists(file_path):
        # [핵심] download_name에 원래 한글 이름을 넣어줌
        return send_file(
            file_path,
            as_attachment=True,
            download_name=attachment.File_Name
        )
    return "서버에 파일이 존재하지 않습니다.", 404


# [4] 첨부파일 개별 삭제
@bp.post("/<person_id>/works/file/<int:attachment_id>/delete")
@login_required
def delete_attachment(person_id, attachment_id):
    try:
        attachment = db.session.get(WorkAttachment, attachment_id)
        if not attachment:
            return jsonify({"ok": False, "message": "파일이 없습니다."}), 404

        work_id = attachment.Work_ID

        # DB 삭제
        db.session.delete(attachment)
        db.session.commit()

        # 남은 파일 확인 후 Attachment_YN 업데이트
        remaining_count = db.session.query(WorkAttachment).filter_by(Work_ID=work_id).count()
        if remaining_count == 0:
            work = db.session.get(WorkInfo, work_id)
            if work:
                work.Attachment_YN = "N"
                db.session.commit()

        return jsonify({"ok": True, "message": "파일이 삭제되었습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


# [5] 작업 삭제
@bp.post("/<person_id>/works/<int:work_id>/delete")
@login_required
def delete_work(person_id, work_id):
    try:
        work = db.session.get(WorkInfo, work_id)
        if not work:
            return jsonify({"ok": False, "message": "데이터가 없습니다."}), 404

        # 첨부파일 DB 정보 삭제
        attachments = db.session.query(WorkAttachment).filter_by(Work_ID=work_id).all()
        for att in attachments:
            db.session.delete(att)
            # (선택) 실제 파일 삭제 로직 추가 가능

        db.session.delete(work)
        db.session.commit()
        return jsonify({"ok": True, "message": "삭제되었습니다."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


# [6] 작업 상세 조회 API
@bp.get("/<person_id>/works/<int:work_id>")
def get_work_detail(person_id, work_id):
    work = db.session.get(WorkInfo, work_id)
    if not work:
        return jsonify({"ok": False, "message": "데이터 없음"}), 404

    # 첨부파일 목록 조회
    attachments = db.session.query(WorkAttachment).filter_by(Work_ID=work_id).all()
    file_list = []
    for f in attachments:
        file_list.append({
            "id": f.Attachment_ID,
            "name": f.File_Name,
            "size": f.File_Size
        })

    return jsonify({
        "ok": True,
        "data": {
            "work_id": work.Work_ID,
            "work_date": str(work.Work_Date),
            "type": work.Work_Type,
            "summary": work.Summary,
            "description": work.Description,
            "submitter": work.Submitter,
            "create_date": work.Create_Date.strftime('%Y-%m-%d'),
            "files": file_list
        }
    })