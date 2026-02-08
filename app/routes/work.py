import os
import uuid
from datetime import datetime, date

from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models.work_info import WorkInfo
from ..models.work_attachments import WorkAttachment
from ..models.ctm_people import CTMPeople

bp = Blueprint("work", __name__, url_prefix="/work")

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".txt", ".csv", ".xlsx", ".xls", ".docx", ".pptx",
                      ".zip"}


# [헬퍼] 파일 확장자 확인
def _is_allowed_filename(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


# [헬퍼] 날짜 파싱
def _parse_date(value: str | None) -> date | None:
    if not value: return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


# [헬퍼] 업로드 폴더 절대 경로 구하기 (경로 오류 방지 핵심 함수)
def get_upload_folder():
    # config에 설정된 값이 있으면 사용, 없으면 기본값
    folder = current_app.config.get("UPLOAD_FOLDER")
    if not folder:
        # 기본값: 앱/static/uploads
        folder = os.path.join(current_app.root_path, "static", "uploads")

    # 상대 경로로 설정되어 있다면 절대 경로로 변환
    if not os.path.isabs(folder):
        folder = os.path.join(current_app.root_path, folder)

    return folder


# [헬퍼] 파일 저장 로직 (중복 제거)
def _save_work_file(work_id, file_obj):
    if not file_obj or not file_obj.filename:
        return False

    if not _is_allowed_filename(file_obj.filename):
        return False

    original_name = file_obj.filename
    safe_name = secure_filename(original_name)
    ext = os.path.splitext(safe_name)[1].lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"

    # 절대 경로 가져오기
    upload_dir = get_upload_folder()

    try:
        os.makedirs(upload_dir, exist_ok=True)
    except OSError:
        pass

    file_path = os.path.join(upload_dir, stored_name)
    file_obj.save(file_path)

    size_bytes = os.path.getsize(file_path)

    attachment = WorkAttachment(
        Work_ID=work_id,
        File_Name=original_name,
        File_Path=stored_name,
        File_Size=size_bytes,
        Upload_Date=datetime.now(),
    )
    db.session.add(attachment)
    return True


# -------------------------------------------------------------------------
# View 라우트
# -------------------------------------------------------------------------

@bp.get("")
@login_required
def list_work():
    q = (request.args.get("q") or "").strip()
    date_from = _parse_date(request.args.get("from"))
    date_to = _parse_date(request.args.get("to"))

    query = db.session.query(WorkInfo, CTMPeople).join(CTMPeople, CTMPeople.Person_ID == WorkInfo.Person_ID)

    if q:
        query = query.filter(
            or_(
                CTMPeople.Company.ilike(f"%{q}%"),
                CTMPeople.Last_Name.ilike(f"%{q}%"),
                WorkInfo.Summary.ilike(f"%{q}%"),
                WorkInfo.Submitter.ilike(f"%{q}%"),
            )
        )

    if date_from: query = query.filter(WorkInfo.Work_Date >= date_from)
    if date_to: query = query.filter(WorkInfo.Work_Date <= date_to)

    rows = query.order_by(WorkInfo.Work_Date.desc().nulls_last(), WorkInfo.Work_ID.desc()).limit(500).all()
    people = db.session.query(CTMPeople).order_by(CTMPeople.Company).all()

    return render_template(
        "work/list.html",
        rows=rows,
        people=people,
        filters={"q": q, "from": request.args.get("from", ""), "to": request.args.get("to", "")},
    )


# -------------------------------------------------------------------------
# API 라우트 (AJAX)
# -------------------------------------------------------------------------

@bp.post("/ajax/create")
@login_required
def ajax_create_work():
    person_id = request.form.get("person_id")
    work_date = _parse_date(request.form.get("work_date"))
    work_type = request.form.get("work_type")

    if not person_id or not work_date or not work_type:
        return jsonify({"ok": False, "message": "필수 항목(고객, 날짜, 유형)이 누락되었습니다."}), 400

    item = WorkInfo(
        Person_ID=person_id,
        Work_Date=work_date,
        Work_Type=work_type,
        Summary=request.form.get("summary"),
        Description=request.form.get("description"),
        Submitter=getattr(current_user, 'user_name', 'System'),
        Create_Date=datetime.now(),
        Attachment_YN="N",
    )
    db.session.add(item)
    db.session.flush()

    files = request.files.getlist("files[]")
    has_file = False
    for f in files:
        if _save_work_file(item.Work_ID, f):
            has_file = True

    if has_file:
        item.Attachment_YN = "Y"

    db.session.commit()
    return jsonify({"ok": True, "message": "작업이 등록되었습니다."})


@bp.get("/ajax/<int:work_id>/detail")
@login_required
def ajax_get_work_detail(work_id):
    w = db.session.get(WorkInfo, work_id)
    if not w:
        return jsonify({"ok": False, "message": "데이터 없음"}), 404

    return jsonify({
        "ok": True,
        "data": {
            "work_id": w.Work_ID,
            "person_id": w.Person_ID,
            "work_date": w.Work_Date.isoformat() if w.Work_Date else "",
            "work_type": w.Work_Type,
            "summary": w.Summary,
            "description": w.Description
        }
    })


@bp.post("/ajax/<int:work_id>/update")
@login_required
def ajax_update_work(work_id):
    item = db.session.get(WorkInfo, work_id)
    if not item:
        return jsonify({"ok": False, "message": "작업을 찾을 수 없습니다."}), 404

    item.Person_ID = request.form.get("person_id")
    item.Work_Date = _parse_date(request.form.get("work_date"))
    item.Work_Type = request.form.get("work_type")
    item.Summary = request.form.get("summary")
    item.Description = request.form.get("description")

    # 파일 추가
    files = request.files.getlist("files[]")
    has_new_file = False
    for f in files:
        if _save_work_file(item.Work_ID, f):
            has_new_file = True

    if has_new_file:
        item.Attachment_YN = "Y"

    db.session.commit()
    return jsonify({"ok": True, "message": "작업 정보가 수정되었습니다."})


@bp.post("/ajax/<int:work_id>/delete")
@login_required
def ajax_delete_work(work_id):
    item = db.session.get(WorkInfo, work_id)
    if not item:
        return jsonify({"ok": False, "message": "데이터 없음"}), 404

    # 첨부파일 삭제
    attachments = db.session.query(WorkAttachment).filter_by(Work_ID=work_id).all()
    upload_dir = get_upload_folder()

    for att in attachments:
        try:
            path = os.path.join(upload_dir, att.File_Path)
            if os.path.exists(path): os.remove(path)
        except:
            pass
        db.session.delete(att)

    db.session.delete(item)
    db.session.commit()
    return jsonify({"ok": True, "message": "삭제되었습니다."})


@bp.get("/ajax/<int:work_id>/attachments")
@login_required
def ajax_work_attachments(work_id):
    atts = db.session.query(WorkAttachment).filter_by(Work_ID=work_id).order_by(WorkAttachment.Upload_Date.desc()).all()
    data = [{
        "id": a.Attachment_ID,
        "name": a.File_Name,
        "size": f"{a.File_Size / 1024:.1f} KB",
        # [중요] 여기서 다운로드 URL을 'work.download_attachment'로 생성하여 전달
        "url": url_for("work.download_attachment", attachment_id=a.Attachment_ID)
    } for a in atts]
    return jsonify({"ok": True, "items": data})


@bp.post("/ajax/attachments/<int:attachment_id>/delete")
@login_required
def ajax_delete_attachment(attachment_id):
    att = db.session.get(WorkAttachment, attachment_id)
    if not att:
        return jsonify({"ok": False}), 404

    work_id = att.Work_ID

    # 실제 파일 삭제
    upload_dir = get_upload_folder()
    try:
        path = os.path.join(upload_dir, att.File_Path)
        if os.path.exists(path): os.remove(path)
    except:
        pass

    db.session.delete(att)
    db.session.commit()

    # Attachment_YN 갱신
    remaining = db.session.query(WorkAttachment).filter_by(Work_ID=work_id).count()
    work = db.session.get(WorkInfo, work_id)
    if work:
        work.Attachment_YN = "Y" if remaining > 0 else "N"
        db.session.commit()

    return jsonify({"ok": True})


# [통합 다운로드 라우트]
@bp.route("/attachments/<int:attachment_id>/download")
@login_required
def download_attachment(attachment_id):
    att = db.session.get(WorkAttachment, attachment_id)
    if not att: return "File not found", 404

    # 절대 경로를 사용하여 다운로드 제공
    upload_dir = get_upload_folder()

    try:
        return send_from_directory(upload_dir, att.File_Path, as_attachment=True, download_name=att.File_Name)
    except FileNotFoundError:
        return "File Not Found on Server", 404