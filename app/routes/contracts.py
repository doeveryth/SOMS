from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime
from ..extensions import db
from ..models.contracts import Contract

bp = Blueprint('contract', __name__, url_prefix='/contract')


# [조회 API]
@bp.get('/ajax/<person_id>')
@login_required
def ajax_list_contracts(person_id):
    contracts = Contract.query.filter_by(Person_ID=person_id) \
        .filter(Contract.Deleted_YN == 'N') \
        .order_by(Contract.Contract_ID.desc()).all()

    data = [{
        'id': c.Contract_ID,
        'service_type': c.Service_Type,  # [추가됨]
        'service_number': c.Service_Number,
        'status': c.Service_Status,
        'amount': c.Contract_Amount,
        'open_date': c.Open_Date.isoformat() if c.Open_Date else '',
        'terminate_date': c.Terminate_Date.isoformat() if c.Terminate_Date else '',
        'note': c.Contract_Note
    } for c in contracts]
    return jsonify({'ok': True, 'data': data})


# [등록 API]
@bp.post('/ajax/create')
@login_required
def ajax_create_contract():
    try:
        def parse_date(d_str):
            return datetime.strptime(d_str, '%Y-%m-%d').date() if d_str else None

        new_c = Contract(
            Person_ID=request.form.get('person_id'),
            Service_Type=request.form.get('service_type'),  # [추가됨]
            Service_Number=request.form.get('service_number'),
            Service_Status=request.form.get('service_status'),
            Contract_Amount=request.form.get('contract_amount'),
            Open_Date=parse_date(request.form.get('open_date')),
            Terminate_Date=parse_date(request.form.get('terminate_date')),
            Contract_Note=request.form.get('contract_note'),
            Deleted_YN='N'
        )
        db.session.add(new_c)
        db.session.commit()
        return jsonify({'ok': True, 'message': '계약이 등록되었습니다.'})
    except Exception as e:
        return jsonify({'ok': False, 'message': str(e)}), 500


# [삭제] Soft Delete 적용 (Update Deleted_YN = 'Y')
@bp.post('/ajax/<int:contract_id>/delete')
@login_required
def ajax_delete_contract(contract_id):
    c = db.session.get(Contract, contract_id)
    if c:
        c.Deleted_YN = 'Y'
        c.Deleted_At = datetime.now()
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'message': '정보 없음'}), 404