# account_routes.py
from __future__ import annotations

import os
import uuid
from werkzeug.utils import secure_filename

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, abort
)
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf

from extensions import db
from models import Student

account_bp = Blueprint("account", __name__, url_prefix="/account")

ALLOWED_EXTS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


def _home_url():
    role = (getattr(current_user, "role", "student") or "student").strip().lower()
    if role == "admin":
        return url_for("admin.admin_home")
    if role == "manager":
        return url_for("manager.manager_home")
    return url_for("student.student_home")


@account_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    # luôn truyền home_url để template có nút "Quay lại"
    home_url = _home_url()

    if request.method == "GET":
        return render_template("account/profile.html", home_url=home_url)

    # POST
    validate_csrf(request.form.get("csrf_token", ""))

    # ---------- cập nhật thông tin ----------
    ten_sv = (request.form.get("ten_sv") or "").strip()
    email = (request.form.get("email") or "").strip()
    gioi_tinh = (request.form.get("gioi_tinh") or "").strip()  # Nam/Nữ/Khác/...
    dia_chi = (request.form.get("dia_chi") or "").strip()

    if not ten_sv:
        flash("Họ và tên không được để trống.", "danger")
        return redirect(url_for("account.profile"))

    if not email:
        flash("Email không được để trống.", "danger")
        return redirect(url_for("account.profile"))

    # Nếu đổi email -> check trùng (trừ chính mình)
    exist = Student.query.filter(Student.email == email, Student.id != current_user.id).first()
    if exist:
        flash("Email đã được dùng bởi tài khoản khác.", "danger")
        return redirect(url_for("account.profile"))

    current_user.ten_sv = ten_sv
    current_user.email = email
    current_user.gioi_tinh = gioi_tinh or None
    current_user.dia_chi = dia_chi or None

    # ---------- upload avatar (nếu có) ----------
    file = request.files.get("avatar")
    if file and file.filename:
        if not _allowed_file(file.filename):
            flash("Avatar chỉ nhận png/jpg/jpeg/gif/webp.", "danger")
            return redirect(url_for("account.profile"))

        ext = file.filename.rsplit(".", 1)[1].lower()
        new_name = secure_filename(f"{uuid.uuid4().hex}.{ext}")

        upload_folder = current_app.config.get("UPLOAD_FOLDER")
        if not upload_folder:
            flash("Thiếu cấu hình UPLOAD_FOLDER trong app.py", "danger")
            return redirect(url_for("account.profile"))

        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, new_name)
        file.save(save_path)

        # xóa avatar cũ
        if getattr(current_user, "avatar", None):
            old_path = os.path.join(upload_folder, current_user.avatar)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass

        current_user.avatar = new_name

    db.session.commit()
    flash("Đã cập nhật hồ sơ!", "success")
    return redirect(url_for("account.profile"))


@account_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    home_url = _home_url()

    if request.method == "GET":
        return render_template("account/change_password.html", home_url=home_url)

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
