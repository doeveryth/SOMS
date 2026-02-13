from datetime import datetime, date

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_

from ..extensions import db
from ..models.sr_ticket import SRTicket
from ..models.ctm_people import CTMPeople

bp = Blueprint("sr", __name__, url_prefix="/sr")


def _parse_date(value: str | None) -> date | None:
    if not value: return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _clean(value: str | None) -> str | None:
    if value is None: return None
    v = value.strip()
    return v if v else None


@bp.route("/list", methods=["GET"])
@login_required
def list_sr():
    # 1. 검색 조건 받기
    location = (request.args.get("location") or "").strip()
    company = (request.args.get("company") or "").strip()
    content = (request.args.get("content") or "").strip()
    date_from_str = request.args.get("from", "")
    date_to_str = request.args.get("to", "")
    date_from = _parse_date(date_from_str)
    date_to = _parse_date(date_to_str)

    # [수정] 페이지 번호 받기 (기본 1)
    page = request.args.get('page', 1, type=int)

    # 2. 쿼리 구성
    query = SRTicket.query  # db.session.query(SRTicket) 과 동일

    if location: query = query.filter(SRTicket.location.ilike(f"%{location}%"))
    if company: query = query.filter(SRTicket.company.ilike(f"%{company}%"))
    if content: query = query.filter(SRTicket.content.ilike(f"%{content}%"))
    if date_from: query = query.filter(SRTicket.request_date >= date_from)
    if date_to: query = query.filter(SRTicket.request_date <= date_to)

    # 3. 정렬 및 페이지네이션
    # 최신순 정렬
    query = query.order_by(SRTicket.request_date.desc(), SRTicket.sr_id.desc())

    # [수정] paginate 적용 (한 페이지당 10개)
    per_page = 10
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 사이트 목록 (모달용)
    customers = CTMPeople.query.order_by(CTMPeople.Company, CTMPeople.Last_Name).all()

    return render_template(
        "sr/list.html",
        pagination=pagination,  # items 대신 pagination 객체 전달
        customers=customers,
        filters={
            "location": location,
            "company": company,
            "content": content,
            "from": date_from_str,
            "to": date_to_str,
        },
    )


@bp.get("/ajax/<int:sr_id>")
@login_required
def ajax_get_sr_detail(sr_id):
    item = db.session.get(SRTicket, sr_id)
    if not item:
        return jsonify({"ok": False, "message": "데이터 없음"}), 404

    return jsonify({
        "ok": True,
        "data": {
            "sr_id": item.sr_id,
            "location": item.location,
            "company": item.company,
            "category": item.category,
            "severity": item.severity,
            "requester": item.requester,
            "request_date": item.request_date.isoformat() if item.request_date else "",
            "content": item.content,
            "handler": item.handler,
            "handled_date": item.handled_date.isoformat() if item.handled_date else "",
            "result": item.result,
            "remark": item.remark
        }
    })


@bp.post("/ajax/create")
@login_required
def ajax_create_sr():
    location = (request.form.get("location") or "").strip()
    company = (request.form.get("company") or "").strip()

    category = _clean(request.form.get("category"))
    severity = _clean(request.form.get("severity"))
    requester = _clean(request.form.get("requester"))

    request_date = _parse_date(request.form.get("request_date"))
    content = (request.form.get("content") or "").strip()

    handler = (request.form.get("handler") or "").strip()
    handled_date = _parse_date(request.form.get("handled_date"))

    result = _clean(request.form.get("result"))
    remark = _clean(request.form.get("remark"))

    if not location or not company or not request_date or not content:
        return jsonify({"ok": False, "message": "필수 항목(위치, 고객사, 요청일, 내용)이 누락되었습니다."}), 400

    item = SRTicket(
        location=location,
        company=company,
        category=category,
        severity=severity,
        requester=requester,
        request_date=request_date,
        content=content,
        handler=handler,
        handled_date=handled_date,
        result=result,
        remark=remark,
        created_by=getattr(current_user, 'user_id', 'System'),
        created_at=datetime.utcnow(),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"ok": True, "id": item.sr_id})


@bp.post("/ajax/<int:sr_id>/update")
@login_required
def ajax_update_sr(sr_id: int):
    item = db.session.get(SRTicket, sr_id)
    if not item:
        return jsonify({"ok": False, "message": "SR을 찾을 수 없습니다."}), 404

    item.location = request.form.get("location")
    item.company = request.form.get("company")
    item.category = _clean(request.form.get("category"))
    item.severity = _clean(request.form.get("severity"))
    item.requester = _clean(request.form.get("requester"))
    item.request_date = _parse_date(request.form.get("request_date"))
    item.content = request.form.get("content")
    item.handler = request.form.get("handler")
    item.handled_date = _parse_date(request.form.get("handled_date"))
    item.result = _clean(request.form.get("result"))
    item.remark = _clean(request.form.get("remark"))

    item.updated_by = getattr(current_user, 'user_id', 'System')
    item.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"ok": True})


@bp.post("/ajax/<int:sr_id>/delete")
@login_required
def ajax_delete_sr(sr_id: int):
    item = db.session.get(SRTicket, sr_id)
    if not item:
        return jsonify({"ok": False, "message": "SR을 찾을 수 없습니다."}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"ok": True})