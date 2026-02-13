from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from app.models.user import User  # 모델 경로 확인

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        user = User.query.filter_by(user_id=user_id).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            # [핵심] 최초 로그인(비번 변경 필요) 체크
            if user.must_change_password:
                flash('최초 로그인입니다. 보안을 위해 비밀번호를 변경해주세요.', 'warning')
                return redirect(url_for('auth.change_password'))

            return redirect(url_for('dashboard.index'))
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃 되었습니다.', 'info')
    return redirect(url_for('auth.login'))


# [핵심] 비밀번호 변경 페이지 라우트
@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')

        if not new_pw or not confirm_pw:
            flash('비밀번호를 입력해주세요.', 'danger')
        elif new_pw != confirm_pw:
            flash('비밀번호가 일치하지 않습니다.', 'danger')
        else:
            # 1. 새 비밀번호로 업데이트
            current_user.password_hash = generate_password_hash(new_pw)
            # 2. 변경 강제 해제
            current_user.must_change_password = False

            db.session.commit()

            flash('비밀번호가 변경되었습니다. 다시 로그인해주세요.', 'success')
            logout_user()  # 보안상 재로그인 유도
            return redirect(url_for('auth.login'))

    return render_template('auth/change_password.html')