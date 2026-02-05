from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from ..extensions import db
from ..models.user import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.get("/login")
def login():
    return render_template("auth/login.html")


@bp.post("/login")
def login_post():
    user_id = request.form.get("user_id", "").strip()
    password = request.form.get("password", "")

    user = db.session.get(User, user_id)
    if not user or not user.is_active or not check_password_hash(user.password_hash, password):
        flash("로그인 정보가 올바르지 않습니다.", "danger")
        return redirect(url_for("auth.login"))

    login_user(user)
    return redirect(url_for("dashboard.index"))


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))