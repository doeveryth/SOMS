from datetime import datetime, date

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_

from ..extensions import db
from ..models.sr_ticket import SRTicket

bp = Blueprint("sr", __name__, url_prefix="/sr")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    return v if v else None


@bp.get("")
@login_required
def list_sr():
    location = (request.args.get("location") or "").strip()
    company = (request.args.get("company") or "").strip()
    content = (request.args.get("content") or "").strip()
    date_from = _parse_date(request.args.get("from"))
    date_to = _parse_date(request.args.get("to"))

    query = db.session.query(SRTicket)

    filters = []
    if location:
        filters.append(SRTicket.location.ilike(f"%{location}%"))
    if company:
        filters.append(SRTicket.company.ilike(f"%{company}%"))
    if content:
        filters.append(SRTicket.content.ilike(f"%{content}%"))
    if date_from:
        filters.append(SRTicket.request_date >= date_from)
    if date_to:
        filters.append(SRTicket.request_date <= date_to)

    if filters:
        query = query.filter(and_(*filters))

    items = query.order_by(SRTicket.request_date.desc(), SRTicket.sr_id.desc()).limit(500).all()

    return render_template(
        "sr/list.html",
        items=items,
        filters={
            "location": location,
            "company": company,
            "content": content,
            "from": request.args.get("from", ""),
            "to": request.args.get("to", ""),
        },
    )


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

    if not location or not company or not request_date or not content or not handler:
        return jsonify({"ok": False, "message": "위치/고객사/요청일/내용/처리자는 필수입니다."}), 400

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
        created_by=current_user.user_id,
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

    if not location or not company or not request_date or not content or not handler:
        return jsonify({"ok": False, "message": "위치/고객사/요청일/내용/처리자는 필수입니다."}), 400

    item.location = location
    item.company = company
    item.category = category
    item.severity = severity
    item.requester = requester
    item.request_date = request_date
    item.content = content
    item.handler = handler
    item.handled_date = handled_date
    item.result = result
    item.remark = remark
    item.updated_by = current_user.user_id
    item.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"ok": True})


@bp.post("/ajax/<int:sr_id>/delete")
@login_required
def ajax_delete_sr(sr_id: int):
    item = db.session.get(SRTicket, sr_id)
    if not item:
        return jsonify({"ok": False, "message": "SR을 찾을 수 없습니다."}), 404

    db.session.delete(item)  # 요구사항: 진짜 삭제
    db.session.commit()
    return jsonify({"ok": True})