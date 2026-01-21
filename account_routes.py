# account_routes.py
from __future__ import annotations

import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf
from werkzeug.utils import secure_filename

from extensions import db
from models import Student

account_bp = Blueprint("account", __name__, url_prefix="/account")

ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _upload_dir() -> str:
    path = os.path.join(current_app.root_path, "static", "uploads")
    os.makedirs(path, exist_ok=True)
    return path


@account_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "GET":
        return render_template("account/profile.html")

    # POST
    validate_csrf(request.form.get("csrf_token", ""))

    # ========== 1) Nếu có upload avatar ==========
    f = request.files.get("avatar")
    if f and f.filename:
        filename = secure_filename(f.filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_EXTS:
            flash("Chỉ nhận ảnh: PNG/JPG/JPEG/GIF/WEBP", "danger")
            return redirect(url_for("account.profile"))

        # xóa ảnh cũ
        if current_user.avatar:
            old_path = os.path.join(_upload_dir(), current_user.avatar)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        new_name = f"{uuid.uuid4().hex}{ext}"
        f.save(os.path.join(_upload_dir(), new_name))

        current_user.avatar = new_name
        db.session.commit()
        flash("Đã cập nhật ảnh đại diện!", "success")
        return redirect(url_for("account.profile"))

    # ========== 2) Nếu không upload avatar -> update info ==========
    ten_sv = (request.form.get("ten_sv") or "").strip()
    email = (request.form.get("email") or "").strip()
    gioi_tinh = (request.form.get("gioi_tinh") or "").strip()
    dia_chi = (request.form.get("dia_chi") or "").strip()

    if not ten_sv:
        flash("Họ và tên không được để trống.", "danger")
        return redirect(url_for("account.profile"))

    if not email:
        flash("Email không được để trống.", "danger")
        return redirect(url_for("account.profile"))

    exist = Student.query.filter(Student.email == email, Student.id != current_user.id).first()
    if exist:
        flash("Email đã được dùng bởi tài khoản khác.", "danger")
        return redirect(url_for("account.profile"))

    current_user.ten_sv = ten_sv
    current_user.email = email
    current_user.gioi_tinh = gioi_tinh or None
    current_user.dia_chi = dia_chi or None

    db.session.commit()
    flash("Đã cập nhật hồ sơ!", "success")
    return redirect(url_for("account.profile"))


@account_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "GET":
        return render_template("account/change_password.html")

    validate_csrf(request.form.get("csrf_token", ""))

    old_password = (request.form.get("old_password") or "").strip()
    new_password = (request.form.get("new_password") or "").strip()
    confirm_password = (request.form.get("confirm_password") or "").strip()

    if not old_password or not new_password or not confirm_password:
        flash("Vui lòng nhập đầy đủ thông tin.", "danger")
        return redirect(url_for("account.change_password"))

    if not current_user.check_password(old_password):
        flash("Mật khẩu hiện tại không đúng.", "danger")
        return redirect(url_for("account.change_password"))

    if len(new_password) < 6:
        flash("Mật khẩu mới phải từ 6 ký tự trở lên.", "danger")
        return redirect(url_for("account.change_password"))

    if new_password != confirm_password:
        flash("Xác nhận mật khẩu không khớp.", "danger")
        return redirect(url_for("account.change_password"))

    current_user.set_password(new_password)
    db.session.commit()

    flash("Đổi mật khẩu thành công!", "success")
    return redirect(url_for("account.change_password"))
