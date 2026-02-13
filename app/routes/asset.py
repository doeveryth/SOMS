from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify,flash,url_for, redirect
from flask_login import login_required, current_user
from sqlalchemy import or_, desc

from ..extensions import db
from ..models.ast_computersystem import AST_Computer_System
from ..models.ctm_people import CTMPeople
from ..models.servers import ServerInfo

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
        ci_name = request.form.get('ci_name', '').strip()
        owner_name = request.form.get('owner_name', '').strip()  # 폼에서 직접 받음

        # 1. 필수값 체크
        if not person_id:
            return jsonify({'ok': False, 'message': '고객사 정보(Person_ID)가 누락되었습니다.'})
        if not ci_name or not owner_name:
            return jsonify({'ok': False, 'message': 'CI 이름과 사이트명은 필수입니다.'})

        # [수정 핵심] 고객 정보 조회 (PK가 아닌 Person_ID 컬럼으로 검색)
        customer = db.session.query(CTMPeople).filter(CTMPeople.Person_ID == person_id).first()
        if not customer:
            return jsonify({'ok': False, 'message': '존재하지 않는 고객사입니다.'})

        # 2. Asset 객체 가져오기 또는 생성
        if asset_id:
            asset = db.session.get(AST_Computer_System, asset_id)
            if not asset:
                return jsonify({'ok': False, 'message': '수정할 장비 정보를 찾을 수 없습니다.'})
        else:
            asset = AST_Computer_System()
            asset.Submitter = getattr(current_user, 'user_name', 'System')

        # 3. 기본 정보 매핑
        asset.Person_ID = person_id
        asset.Name = ci_name
        asset.Owner_name = owner_name       # 입력받은 사이트명
        asset.Company = customer.Company    # [수정] 위에서 조회한 customer 객체의 회사명 사용

        # 4. 분류 정보
        asset.Category = request.form.get('category')
        asset.Type = request.form.get('type')
        asset.Item = request.form.get('item')

        # 5. 제품 정보
        asset.Supplier = request.form.get('supplier')
        asset.Product_Name = request.form.get('product_name')
        asset.Model_Number = request.form.get('model_number')
        asset.Manufacturer_Name = request.form.get('manufacturer_name')

        # 6. 상세 식별 정보
        asset.Serial_Number = request.form.get('serial_number')
        asset.Version_Number = request.form.get('os_version')
        asset.IP_Address = request.form.get('ip_address')
        asset.Region = request.form.get('region')
        asset.IDC_Site = request.form.get('idc_site')
        asset.Short_Description = request.form.get('ci_note')
        asset.Description = request.form.get('description')

        # 7. 운영 정보
        asset.Maintenance_Company = request.form.get('maintenance_company')
        asset.Operation_Company = request.form.get('operation_company')
        asset.Operation_Mode = request.form.get('operation_mode')

        # 8. 백업 설정
        asset.C_backup = request.form.get('c_backup')
        asset.C_cycle = request.form.get('c_cycle')
        asset.C_note = request.form.get('cfg_note')

        # 9. 날짜 및 상태
        asset.AssetLifecycleStatus = request.form.get('lifecycle_status')
        asset.PurchaseDate = _parse_date(request.form.get('purchase_date'))
        asset.Receive_Date = _parse_date(request.form.get('receive_date')) # 입고일 추가
        asset.InstallationDate = _parse_date(request.form.get('installation_date'))
        asset.ReturnDate = _parse_date(request.form.get('return_date')) # 반환일 추가
        asset.License_Expiry_Date = _parse_date(request.form.get('license_expiry'))
        asset.Disposal_Date = _parse_date(request.form.get('disposal_date'))

        # 신규 등록인 경우 세션에 추가
        if not asset_id:
            db.session.add(asset)

        db.session.commit()
        return jsonify({'ok': True})

    except Exception as e:
        db.session.rollback()
        # 에러 로그를 콘솔에도 출력해서 확인하기 쉽도록 함
        print(f"Asset Save Error: {str(e)}")
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


# ==============================================================
# [NEW] 서버 자산 전체 조회 및 등록 페이지
# ==============================================================
# ==============================================================
# [NEW] 서버 자산 전체 조회 및 등록 페이지
# ==============================================================
@bp.route('/servers', methods=['GET', 'POST'])
@login_required
def list_servers():
    # 1. [POST] 신규 서버 등록
    if request.method == 'POST':
        try:
            person_id = request.form.get('Person_ID')
            server_name = request.form.get('server_name')
            server_ip = request.form.get('server_ip')

            if not person_id or not server_name:
                flash('고객사와 서버 이름은 필수 항목입니다.', 'danger')
                return redirect(url_for('asset.list_servers'))

            submitter = getattr(current_user, 'User_Name', getattr(current_user, 'name', 'System'))

            new_server = ServerInfo(
                Person_ID=person_id,
                chServerName=server_name,
                chServerInfo=server_ip,
                Submitter=submitter,
                Create_Date=datetime.now()
            )
            db.session.add(new_server)
            db.session.commit()
            flash('서버가 성공적으로 등록되었습니다.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'등록 중 오류 발생: {str(e)}', 'danger')

        return redirect(url_for('asset.list_servers'))

    # 2. [GET] 목록 조회 (페이지네이션 + 검색)
    page = request.args.get('page', 1, type=int)  # 페이지 번호
    q = request.args.get('q', '')

    query = db.session.query(ServerInfo, CTMPeople) \
        .join(CTMPeople, ServerInfo.Person_ID == CTMPeople.Person_ID)

    if q:
        search = f"%{q}%"
        query = query.filter(or_(
            ServerInfo.chServerName.ilike(search),
            ServerInfo.chServerInfo.ilike(search),
            CTMPeople.Company.ilike(search)
        ))

    # [수정] paginate 적용 (한 페이지당 15개)
    per_page = 15
    pagination = query.order_by(desc(ServerInfo.Create_Date)) \
        .paginate(page=page, per_page=per_page, error_out=False)

    # 등록 모달용 전체 고객 리스트
    customers = CTMPeople.query.order_by(CTMPeople.Company).all()

    return render_template(
        'asset/server_list.html',
        pagination=pagination,  # rows 대신 pagination 객체 전달
        customers=customers,
        q=q
    )