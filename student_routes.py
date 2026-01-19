from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from auth import roles_required
from models import Subject, Lesson, Exam, Grade, Class  # dùng model bạn đã tạo

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.get("/home")
@login_required
@roles_required("student", "admin", "manager")  # admin/manager vẫn vào xem nếu muốn
def student_home():
    return render_template("student/home.html")


# ----------------------------
# 1) BẢNG ĐIỂM (chỉ xem điểm của mình)
# ----------------------------
@student_bp.get("/grades")
@login_required
@roles_required("student", "admin", "manager")
def student_grades():
    rows = (
        Grade.query
        .filter(Grade.student_id == current_user.id)
        .order_by(Grade.id.desc())
        .all()
    )
    return render_template("student/grades.html", rows=rows)


# ----------------------------
# 2) MÔN HỌC (danh sách môn)
# ----------------------------
@student_bp.get("/subjects")
@login_required
@roles_required("student", "admin", "manager")
def student_subjects():
    q = (request.args.get("q") or "").strip()
    query = Subject.query
    if q:
        query = query.filter(
            (Subject.code.ilike(f"%{q}%")) |
            (Subject.name.ilike(f"%{q}%"))
        )
    subjects = query.order_by(Subject.name.asc()).all()
    return render_template("student/subjects.html", subjects=subjects, q=q)


# ----------------------------
# 3) BÀI HỌC (lọc theo môn)
# ----------------------------
@student_bp.get("/lessons")
@login_required
@roles_required("student", "admin", "manager")
def student_lessons():
    subject_id = request.args.get("subject_id", type=int)

    subjects = Subject.query.order_by(Subject.name.asc()).all()

    query = Lesson.query
    if subject_id:
        query = query.filter(Lesson.subject_id == subject_id)

    lessons = query.order_by(Lesson.subject_id.asc(), Lesson.order_no.asc()).all()

    return render_template(
        "student/lessons.html",
        lessons=lessons,
        subjects=subjects,
        subject_id=subject_id
    )


# ----------------------------
# 4) KỲ THI (lọc theo môn)
# ----------------------------
@student_bp.get("/exams")
@login_required
@roles_required("student", "admin", "manager")
def student_exams():
    subject_id = request.args.get("subject_id", type=int)

    subjects = Subject.query.order_by(Subject.name.asc()).all()

    query = Exam.query
    if subject_id:
        query = query.filter(Exam.subject_id == subject_id)

    exams = query.order_by(Exam.exam_date.desc().nullslast(), Exam.id.desc()).all()

    return render_template(
        "student/exams.html",
        exams=exams,
        subjects=subjects,
        subject_id=subject_id
    )


# ----------------------------
# 5) LỚP HỌC (hiện tất cả lớp + môn trong lớp)
# (vì bạn chưa có mapping student->class rõ, nên hiện list lớp để xem)
# ----------------------------
@student_bp.get("/classes")
@login_required
@roles_required("student", "admin", "manager")
def student_classes():
    q = (request.args.get("q") or "").strip()
    query = Class.query
    if q:
        query = query.filter(
            (Class.code.ilike(f"%{q}%")) |
            (Class.name.ilike(f"%{q}%"))
        )
    classes = query.order_by(Class.name.asc()).all()
    return render_template("student/classes.html", classes=classes, q=q)
