from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf

from extensions import db
from models import Notification

noti_bp = Blueprint("noti", __name__, url_prefix="/notifications")


@noti_bp.get("/")
@login_required
def index():
    items = (Notification.query
             .filter_by(user_id=current_user.id)
             .order_by(Notification.created_at.desc())
             .all())
    return render_template("notifications/index.html", items=items)


@noti_bp.post("/<int:noti_id>/read")
@login_required
def mark_read(noti_id: int):
    validate_csrf(request.form.get("csrf_token", ""))

    n = Notification.query.filter_by(id=noti_id, user_id=current_user.id).first()
    if n:
        n.is_read = True
        db.session.commit()
    return redirect(url_for("noti.index"))


@noti_bp.post("/read-all")
@login_required
def mark_all_read():
    validate_csrf(request.form.get("csrf_token", ""))

    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(url_for("noti.index"))
