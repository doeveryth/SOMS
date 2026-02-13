import os
import uuid
from datetime import datetime, date

from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models.work_info import WorkInfo
from ..models.work_attachments import WorkAttachment
from ..models.ctm_people import CTMPeople

bp = Blueprint("work", __name__, url_prefix="/work")

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".txt", ".csv", ".xlsx", ".xls", ".docx", ".pptx",
                      ".zip"}


# -------------------------------------------------------------------------
# [헬퍼 함수] 파일 및 경로 처리
# -------------------------------------------------------------------------
def _is_allowed_filename(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXTENSIONS


def _parse_date(value: str | None) -> date | None:
    if not value: return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_upload_folder():
    folder = current_app.config.get("UPLOAD_FOLDER")
    if not folder:
        folder = os.path.join(current_app.root_path, "static", "uploads")
    if not os.path.isabs(folder):
        folder = os.path.join(current_app.root_path, folder)
    return folder


def _save_work_file(work_id, file_obj):
    if not file_obj or not file_obj.filename:
        return False
    if not _is_allowed_filename(file_obj.filename):
        return False

    original_name = file_obj.filename
    safe_name = secure_filename(original_name)
    ext = os.path.splitext(safe_name)[1].lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
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
# [View 라우트]
# -------------------------------------------------------------------------

@bp.route("/list", methods=["GET"])
@login_required
def list_work():
    # 1. 파라미터 수신
    q = (request.args.get("q") or "").strip()
    date_from = _parse_date(request.args.get("from"))
    date_to = _parse_date(request.args.get("to"))

    # [수정됨] 페이지 번호 받기 (기본값 1)
    page = request.args.get('page', 1, type=int)

    # 2. 쿼리 구성 (WorkInfo + CTMPeople 조인)
    query = db.session.query(WorkInfo, CTMPeople).join(CTMPeople, CTMPeople.Person_ID == WorkInfo.Person_ID)

    # 3. 필터링
    if q:
        query = query.filter(
            or_(
                CTMPeople.Company.ilike(f"%{q}%"),
                CTMPeople.Last_Name.ilike(f"%{q}%"),
                WorkInfo.Summary.ilike(f"%{q}%"),
                WorkInfo.Submitter.ilike(f"%{q}%"),
            )
        )
    if date_from:
        query = query.filter(WorkInfo.Work_Date >= date_from)
    if date_to:
        query = query.filter(WorkInfo.Work_Date <= date_to)

    # 4. 정렬 및 페이지네이션
    # 최신 날짜순, 그리고 ID 역순 정렬
    query = query.order_by(WorkInfo.Work_Date.desc().nulls_last(), WorkInfo.Work_ID.desc())

    # [수정됨] paginate 적용 (한 페이지당 10개)
    per_page = 10
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 5. 등록 모달(Select2)에서 사용할 전체 고객 리스트
    people = db.session.query(CTMPeople).order_by(CTMPeople.Company).all()

    return render_template(
        "work/list.html",
        pagination=pagination,  # rows 대신 pagination 객체 전달
        people=people,
        filters={"q": q, "from": request.args.get("from", ""), "to": request.args.get("to", "")},
        today_date=datetime.now().strftime('%Y-%m-%d')
    )


# -------------------------------------------------------------------------
# [API 라우트] (AJAX) - 기존 로직 유지
# -------------------------------------------------------------------------

@bp.post("/ajax/create")
@login_required
def ajax_create_work():
    person_id = request.form.get("person_id")
    work_date = _parse_date(request.form.get("work_date"))
    work_type = request.form.get("work_type")

    # 필수값 검증
    if not person_id or not work_date or not work_type:
        return jsonify({"ok": False, "message": "필수 항목(고객, 날짜, 유형)이 누락되었습니다."}), 400

    # Submitter: 현재 로그인한 사용자 이름 (없으면 System)
    submitter = getattr(current_user, 'user_name', getattr(current_user, 'name', 'System'))

    item = WorkInfo(
        Person_ID=person_id,
        Work_Date=work_date,
        Work_Type=work_type,
        Summary=request.form.get("summary"),
        Description=request.form.get("description"),
        Submitter=submitter,
        Create_Date=datetime.now(),
        Attachment_YN="N",
    )
    db.session.add(item)
    db.session.flush()  # ID 생성을 위해 flush

    # 파일 저장
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
    upload_dir = get_upload_folder()
    try:
        path = os.path.join(upload_dir, att.File_Path)
        if os.path.exists(path): os.remove(path)
    except:
        pass

    db.session.delete(att)
    db.session.commit()

    remaining = db.session.query(WorkAttachment).filter_by(Work_ID=work_id).count()
    work = db.session.get(WorkInfo, work_id)
    if work:
        work.Attachment_YN = "Y" if remaining > 0 else "N"
        db.session.commit()

    return jsonify({"ok": True})


@bp.route("/attachments/<int:attachment_id>/download")
@login_required
def download_attachment(attachment_id):
    att = db.session.get(WorkAttachment, attachment_id)
    if not att: return "File not found", 404

    upload_dir = get_upload_folder()
    try:
        return send_from_directory(upload_dir, att.File_Path, as_attachment=True, download_name=att.File_Name)
    except FileNotFoundError:
        return "File Not Found on Server", 404