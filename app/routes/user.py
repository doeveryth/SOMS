from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user
from sqlalchemy import or_
from datetime import datetime

from app import db
from app.models.user import User  # 모델 경로 확인

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('/list', methods=['GET', 'POST'])
@login_required
def list_users():
    # 1. [POST] 사용자 등록/수정
    if request.method == 'POST':
        try:
            target_id = request.form.get('target_id')

            user_id = request.form.get('user_id')
            user_name = request.form.get('user_name')
            password = request.form.get('password')
            role = request.form.get('role', 'User')
            email = request.form.get('email')
            department = request.form.get('department')

            if target_id:
                # [수정 모드]
                user = User.query.filter_by(user_id=target_id).first()
                if user:
                    user.user_name = user_name
                    user.role = role
                    user.email = email
                    user.department = department
                    # 비밀번호 입력 시에만 변경
                    if password and password.strip():
                        user.password_hash = generate_password_hash(password)
                        # 관리자가 직접 비번을 바꿔줬으므로 변경 강제 해제 (선택사항)
                        user.must_change_password = False

                    db.session.commit()
                    flash('사용자 정보가 수정되었습니다.', 'success')
            else:
                # [신규 등록 모드]
                existing = User.query.filter_by(user_id=user_id).first()
                if existing:
                    flash('이미 존재하는 아이디입니다.', 'danger')
                else:
                    # [핵심] 신규 비밀번호는 무조건 'new1234!'
                    default_pw = 'new1234!'

                    new_user = User(
                        user_id=user_id,
                        user_name=user_name,
                        password_hash=generate_password_hash(default_pw),
                        role=role,
                        email=email,
                        department=department,
                        created_at=datetime.now(),
                        # [핵심] 최초 로그인 시 변경 강제
                        must_change_password=True
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    flash(f'사용자가 생성되었습니다. (초기 비밀번호: {default_pw})', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'오류 발생: {str(e)}', 'danger')

        return redirect(url_for('users.list_users'))

    # 2. [GET] 목록 조회
    q = request.args.get('q', '')
    query = User.query

    if q:
        search = f"%{q}%"
        query = query.filter(or_(
            User.user_id.ilike(search),
            User.user_name.ilike(search),
            User.department.ilike(search)
        ))

    users = query.order_by(User.created_at.desc()).all()

    return render_template('users/list.html', users=users, q=q)


@bp.route('/delete/<string:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if user_id == current_user.user_id:
        flash('본인 계정은 삭제할 수 없습니다.', 'warning')
        return redirect(url_for('users.list_users'))

    try:
        user = User.query.filter_by(user_id=user_id).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            flash('사용자가 삭제되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'삭제 중 오류: {str(e)}', 'danger')

    return redirect(url_for('users.list_users'))