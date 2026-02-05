import os
import uuid
from datetime import datetime, date

import passdb
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory, url_for
from flask_login import login_required, current_user

from sqlalchemy import or_
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models.work_info import WorkInfo
from ..models.work_attachments import WorkAttachment
from ..models.ctm_people import CTMPeople

bp = Blueprint("work", __name__, url_prefix="/work")

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".txt", ".csv", ".xlsx", ".xls", ".docx", ".pptx", ".zip"}


def _is_allowed_filename(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@bp.get("")
@login_required
def list_work():
    q = (request.args.get("q") or "").strip()
    date_from = _parse_date(request.args.get("from"))
    date_to = _parse_date(request.args.get("to"))

    query = (
        db.session.query(WorkInfo, CTMPeople)
        .join(CTMPeople, CTMPeople.Person_ID == WorkInfo.Person_ID)
    )

    if q:
        query = query.filter(
            or_(
                CTMPeople.Company.ilike(f"%{q}%"),
                CTMPeople.Last_Name.ilike(f"%{q}%"),
                WorkInfo.Summary.ilike(f"%{q}%"),
                WorkInfo.Description.ilike(f"%{q}%"),
                WorkInfo.Submitter.ilike(f"%{q}%"),
            )
        )

    if date_from:
        query = query.filter(WorkInfo.Work_Date >= date_from)
    if date_to:
        query = query.filter(WorkInfo.Work_Date <= date_to)

    rows = query.order_by(WorkInfo.Work_Date.desc().nulls_last(), WorkInfo.Work_ID.desc()).limit(500).all()
    people = db.session.query(CTMPeople).order_by(CTMPeople.Company, CTMPeople.Last_Name).all()

    return render_template(
        "work/list.html",
        rows=rows,
        people=people,
        filters={"q": q, "from": request.args.get("from", ""), "to": request.args.get("to", "")},
    )


@bp.post("/ajax/create")
@login_required
def ajax_create_work():
    person_id = (request.form.get("person_id") or "").strip()
    work_date = _parse_date(request.form.get("work_date"))
    work_type = (request.form.get("work_type") or "").strip()
    summary = (request.form.get("summary") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not person_id or not work_date or not work_type:
        return jsonify({"ok": False, "message": "고객/작업유형/작업일은 필수입니다."}), 400

    item = WorkInfo(
        Person_ID=person_id,
        Work_Date=work_date,
        Work_Type=work_type,
        Summary=summary or None,
        Description=description or None,
        Submitter=current_user.user_id,
        Create_Date=datetime.utcnow(),
        Attachment_YN="N",
    )
    db.session.add(item)
    db.session.flush()  # Work_ID 확보

    if "file" in request.files and request.files["file"].filename:
        f = request.files["file"]
        if not _is_allowed_filename(f.filename):
            return jsonify({"ok": False, "message": "허용되지 않은 확장자입니다."}), 400

        original_name = f.filename
        safe_name = secure_filename(original_name)
        ext = os.path.splitext(safe_name)[1].lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"

        upload_dir = current_app.config.get("UPLOAD_FOLDER", "app/static/uploads")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, stored_name)
        f.save(file_path)

        size_bytes = os.path.getsize(file_path)
        max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 500 * 1024 * 1024)
        if size_bytes > max_bytes:
            try:
                os.remove(file_path)
            except OSError:
                pass
            return jsonify({"ok": False, "message": "파일 크기가 제한을 초과했습니다."}), 400
        upload_time = datetime.utcnow().replace(second=0, microsecond=0)
        attachment = WorkAttachment(
            Work_ID=item.Work_ID,
            File_Name=original_name,
            File_Path=stored_name,
            File_Size=size_bytes,
            Upload_Date=upload_time,
        )
        db.session.add(attachment)
        item.Attachment_YN = "Y"

    db.session.commit()
    return jsonify({"ok": True, "id": item.Work_ID})


@bp.post("/ajax/<int:work_id>/update")
@login_required
def ajax_update_work(work_id: int):
    item = db.session.get(WorkInfo, work_id)
    if not item:
        return jsonify({"ok": False, "message": "작업을 찾을 수 없습니다."}), 404

    work_date = _parse_date(request.form.get("work_date"))
    work_type = (request.form.get("work_type") or "").strip()
    summary = (request.form.get("summary") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not work_date or not work_type:
        return jsonify({"ok": False, "message": "작업유형/작업일은 필수입니다."}), 400

    item.Work_Date = work_date
    item.Work_Type = work_type
    item.Summary = summary or None
    item.Description = description or None

    db.session.commit()
    return jsonify({"ok": True})



@bp.post("/ajax/<int:work_id>/delete")
@login_required
def ajax_delete_work(work_id: int):
    item = db.session.get(WorkInfo, work_id)
    if not item:
        return jsonify({"ok": False, "message": "작업을 찾을 수 없습니다."}), 404

    # 먼저 연관된 첨부파일 삭제
    attachments = (
        db.session.query(WorkAttachment)
        .filter(WorkAttachment.Work_ID == work_id)
        .all()
    )
    for attachment in attachments:
        # 파일 시스템에서도 삭제
        upload_dir = current_app.config.get("UPLOAD_FOLDER", "app/static/uploads")
        file_path = os.path.join(upload_dir, attachment.File_Path)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
        db.session.delete(attachment)

    # 그 다음 작업 삭제
    db.session.delete(item)
    db.session.commit()
    return jsonify({"ok": True})

@bp.get("/ajax/<int:work_id>/attachments")
@login_required
def ajax_work_attachments(work_id: int):
    attachments = (
        db.session.query(WorkAttachment)
        .filter(WorkAttachment.Work_ID == work_id)
        .order_by(WorkAttachment.Upload_Date.desc())
        .all()
    )

    data = [
        {
            "id": a.Attachment_ID,
            "name": a.File_Name,
            "size": a.File_Size,
            "uploaded_at": a.Upload_Date.replace(second=0, microsecond=0).isoformat() if a.Upload_Date else None,
            "download_url": url_for("work.download_attachment", attachment_id=a.Attachment_ID),
        }
        for a in attachments
    ]
    return jsonify({"ok": True, "items": data})


@bp.post("/ajax/attachments/<int:attachment_id>/delete")
@login_required
def ajax_delete_attachment(attachment_id: int):
    attachment = db.session.get(WorkAttachment, attachment_id)
    if not attachment:
        return jsonify({"ok": False, "message": "첨부파일을 찾을 수 없습니다."}), 404

    work_id = attachment.Work_ID
    db.session.delete(attachment)

    remaining = (
        db.session.query(WorkAttachment)
        .filter(WorkAttachment.Work_ID == work_id)
        .count()
    )
    work = db.session.get(WorkInfo, work_id)
    if work:
        work.Attachment_YN = "Y" if remaining > 0 else "N"

    db.session.commit()
    return jsonify({"ok": True})


@bp.get("/attachments/<int:attachment_id>/download")
@login_required
def download_attachment(attachment_id: int):
    attachment = db.session.get(WorkAttachment, attachment_id)
    if not attachment:
        return "Not Found", 404

    upload_dir = current_app.config.get("UPLOAD_FOLDER", "app/static/uploads")
    return send_from_directory(
        upload_dir,
        attachment.File_Path,
        as_attachment=True,
        download_name=attachment.File_Name,
    )