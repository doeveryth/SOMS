from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_

from ..extensions import db
from ..models.ast_computersystem import AST_Computer_System
from ..models.ctm_people import CTMPeople

bp = Blueprint('asset', __name__, url_prefix='/asset')


def _parse_date(value):
    if not value: return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@bp.route('/security')
@login_required
def list_security():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    company = request.args.get('company', '').strip()
    a_type = request.args.get('type', '').strip()

    query = db.session.query(AST_Computer_System, CTMPeople) \
        .outerjoin(CTMPeople, AST_Computer_System.Person_ID == CTMPeople.Person_ID)

    if q:
        query = query.filter(or_(
            AST_Computer_System.Name.ilike(f'%{q}%'),
            AST_Computer_System.IP_Address.ilike(f'%{q}%'),
            AST_Computer_System.Serial_Number.ilike(f'%{q}%')
        ))
    if company:
        query = query.filter(CTMPeople.Company.ilike(f'%{company}%'))
    if a_type:
        query = query.filter(AST_Computer_System.Type == a_type)

    per_page = 15
    pagination = query.order_by(AST_Computer_System.Asset_ID.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    customers = db.session.query(CTMPeople).order_by(CTMPeople.Company).all()

    return render_template(
        'asset/list.html',
        pagination=pagination,
        customers=customers,
        filters={'q': q, 'company': company, 'type': a_type}
    )


@bp.route('/ajax/save', methods=['POST'])
@login_required
def ajax_save_asset():
    try:
        asset_id = request.form.get('asset_id')
        person_id = request.form.get('person_id')
        ci_name = request.form.get('ci_name', '').strip()  # 공백 제거

        # [수정] 필수값 체크: 고객사 + CI 이름 필수
        if not person_id:
            return jsonify({'ok': False, 'message': '고객사를 선택해주세요.'})
        if not ci_name:
            return jsonify({'ok': False, 'message': 'CI 이름(장비 식별명)은 필수 입력 항목입니다.'})

        # 이름 중복 체크 (신규 등록이거나, 수정인데 이름이 바뀐 경우)
        existing = db.session.query(AST_Computer_System).filter_by(Name=ci_name).first()
        if existing:
            # 수정 모드인데 내 ID가 아니면 중복 (즉, 다른 장비가 이미 사용 중)
            if not asset_id or (asset_id and str(existing.Asset_ID) != str(asset_id)):
                return jsonify({'ok': False, 'message': f"이미 존재하는 CI 이름입니다: {ci_name}"})

        # 고객 정보 조회
        customer = db.session.query(CTMPeople).filter_by(Person_ID=person_id).first()
        owner_name = customer.Company if customer else 'Unknown'

        if asset_id:
            asset = db.session.get(AST_Computer_System, asset_id)
            if not asset: return jsonify({'ok': False, 'message': '장비 없음'})
        else:
            asset = AST_Computer_System()
            asset.Owner_name = owner_name
            asset.Company = owner_name
            asset.Submitter = getattr(current_user, 'user_id', 'System')

        # 1. 기본/식별 정보
        asset.Person_ID = person_id
        asset.Name = ci_name  # [수정] 입력받은 이름 그대로 사용
        asset.Owner_name = owner_name

        # 2. 분류 정보
        asset.Category = request.form.get('category')
        asset.Type = request.form.get('type')
        asset.Item = request.form.get('item')

        # 3. 제품 정보
        asset.Supplier = request.form.get('supplier')
        asset.Product_Name = request.form.get('product_name')
        asset.Model_Number = request.form.get('model_number')
        asset.Manufacturer_Name = request.form.get('manufacturer_name')

        # 4. 상세 식별 정보
        asset.Serial_Number = request.form.get('serial_number')
        asset.Version_Number = request.form.get('os_version')
        asset.IP_Address = request.form.get('ip_address')
        asset.Region = request.form.get('region')
        asset.IDC_Site = request.form.get('idc_site')
        asset.Short_Description = request.form.get('ci_note')
        asset.Description = request.form.get('description')

        # 5. 운영 정보
        asset.Maintenance_Company = request.form.get('maintenance_company')
        asset.Operation_Company = request.form.get('operation_company')
        asset.Operation_Mode = request.form.get('operation_mode')

        # 6. 백업 설정
        asset.C_backup = request.form.get('c_backup')
        asset.C_cycle = request.form.get('c_cycle')
        asset.C_note = request.form.get('cfg_note')

        # 7. 날짜 및 상태
        asset.AssetLifecycleStatus = request.form.get('lifecycle_status')
        asset.PurchaseDate = _parse_date(request.form.get('purchase_date'))
        asset.InstallationDate = _parse_date(request.form.get('installation_date'))
        asset.License_Expiry_Date = _parse_date(request.form.get('license_expiry'))
        asset.Disposal_Date = _parse_date(request.form.get('disposal_date'))

        if not asset_id:
            db.session.add(asset)

        # [삭제됨] 자동 이름 생성 로직 (generate_unique_name) 호출 부분 제거

        db.session.commit()
        return jsonify({'ok': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'message': str(e)})


@bp.route('/ajax/<int:asset_id>/delete', methods=['POST'])
@login_required
def ajax_delete_asset(asset_id):
    asset = db.session.get(AST_Computer_System, asset_id)
    if asset:
        db.session.delete(asset)
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'message': '삭제 실패'})