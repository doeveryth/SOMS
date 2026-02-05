import os
import uuid
from flask import Blueprint, current_app, request, redirect, url_for, flash, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime

from ..extensions import db
from ..models.customer_notes import CustomerNote
from ..models.note_attachments import NoteAttachment

bp = Blueprint("uploads", __name__, url_prefix="/uploads")

ALLOWED_EXT = {"png", "jpg", "jpeg", "pdf", "xlsx", "docx", "zip"}


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXT


@bp.post("/notes/<int:note_id>")
@login_required
def upload_note_attachment(note_id: int):
    note = db.session.get(CustomerNote, note_id)
    if not note or note.Deleted_YN == "Y":
        flash("대상 특이사항을 찾을 수 없습니다.", "warning")
        return redirect(url_for("dashboard.index"))

    if "file" not in request.files:
        flash("파일이 없습니다.", "danger")
        return redirect(url_for("customers.detail", person_id=note.Person_ID))

    file = request.files["file"]
    if not file or file.filename == "":
        flash("파일이 선택되지 않았습니다.", "danger")
        return redirect(url_for("customers.detail", person_id=note.Person_ID))

    if not allowed_file(file.filename):
        flash("허용되지 않는 파일 확장자입니다.", "danger")
        return redirect(url_for("customers.detail", person_id=note.Person_ID))

    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[1].lower()
    stored = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    path = os.path.join(upload_dir, stored)
    file.save(path)

    size_bytes = os.path.getsize(path)
    content_type = file.mimetype

    att = NoteAttachment(
        Note_ID=note.Note_ID,
        Original_Filename=original,
        Stored_Filename=stored,
        Content_Type=content_type,
        Size_Bytes=size_bytes,
        Uploaded_By=current_user.user_id,
        Uploaded_At=datetime.utcnow(),
        Deleted_YN="N",
    )
    db.session.add(att)
    db.session.commit()

    flash("첨부파일이 업로드되었습니다.", "success")
    return redirect(url_for("customers.detail", person_id=note.Person_ID))


@bp.get("/files/<path:stored_filename>")
@login_required
def download(stored_filename: str):
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_dir, stored_filename, as_attachment=True)