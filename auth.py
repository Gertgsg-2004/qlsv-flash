# auth.py
from functools import wraps
from urllib.parse import urlparse, urljoin

from flask import Blueprint, request, redirect, url_for, flash, render_template, abort
from flask_login import current_user, login_user

from models import Student

auth_bp = Blueprint("auth", __name__)

# ---------- helper ----------
def is_safe_url(target: str) -> bool:
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def redirect_by_role(user):
    role = (getattr(user, "role", "student") or "student").strip().lower()
    if role == "admin":
        return redirect(url_for("admin.admin_home"))
    if role == "manager":
        return redirect(url_for("manager.manager_home"))
    return redirect(url_for("student.student_home"))


# ✅ decorator phân quyền
def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            user_role = (getattr(current_user, "role", "") or "").strip().lower()
            if user_role not in [r.lower() for r in roles]:
                abort(403)

            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------- LOGIN ----------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user)

    if request.method == "GET":
        return render_template("login.html")  # ❌ không dùng WTForms

    identifier = (request.form.get("identifier") or "").strip()
    password = (request.form.get("password") or "").strip()

    if not identifier or not password:
        flash("Vui lòng nhập đầy đủ thông tin.", "danger")
        return redirect(url_for("auth.login"))

    user = Student.query.filter(
        (Student.email == identifier) | (Student.ma_sv == identifier)
    ).first()

    if not user or not user.check_password(password):
        flash("Sai tài khoản hoặc mật khẩu.", "danger")
        return redirect(url_for("auth.login"))

    login_user(user)

    next_url = request.args.get("next")
    if next_url and is_safe_url(next_url):
        return redirect(next_url)

    return redirect_by_role(user)
