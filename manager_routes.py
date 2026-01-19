# manager_routes.py
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from flask_login import login_required
from flask_wtf.csrf import validate_csrf

from auth import roles_required
from extensions import db
from models import Student, Class, Subject, Exam, Lesson, Grade

manager_bp = Blueprint("manager", __name__, url_prefix="/manager")


# =========================================================
# HOME
# =========================================================
@manager_bp.get("/home")
@login_required
@roles_required("manager")
def manager_home():
    return render_template("manager/home.html")


# =========================================================
# SUBJECTS (GV CRUD toàn quyền)
# =========================================================
@manager_bp.get("/subjects")
@login_required
@roles_required("manager")
def manager_subjects():
    q = (request.args.get("q") or "").strip()

    query = Subject.query
    if q:
        query = query.filter(
            (Subject.code.ilike(f"%{q}%")) |
            (Subject.name.ilike(f"%{q}%"))
        )

    subjects = query.order_by(Subject.id.desc()).all()
    return render_template("manager/subjects.html", subjects=subjects, q=q)


@manager_bp.route("/subjects/new", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_subject_create():
    if request.method == "GET":
        return render_template("manager/subject_form.html", mode="create", subject=None)

    validate_csrf(request.form.get("csrf_token", ""))

    code = (request.form.get("code") or "").strip()
    name = (request.form.get("name") or "").strip()
    credits_raw = (request.form.get("credits") or "3").strip()
    description = (request.form.get("description") or "").strip()

    if not code or not name:
        flash("Vui lòng nhập Code và Tên môn học.", "danger")
        return redirect(url_for("manager.manager_subject_create"))

    try:
        credits = int(credits_raw)
        if credits <= 0:
            raise ValueError()
    except Exception:
        flash("Tín chỉ phải là số nguyên dương.", "danger")
        return redirect(url_for("manager.manager_subject_create"))

    if Subject.query.filter_by(code=code).first():
        flash("Code môn học đã tồn tại.", "danger")
        return redirect(url_for("manager.manager_subject_create"))

    s = Subject(code=code, name=name, credits=credits, description=description or None)
    db.session.add(s)
    db.session.commit()
    flash("Đã thêm môn học!", "success")
    return redirect(url_for("manager.manager_subjects"))


@manager_bp.route("/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_subject_edit(subject_id: int):
    subject = Subject.query.get(subject_id)
    if not subject:
        abort(404)

    if request.method == "GET":
        return render_template("manager/subject_form.html", mode="edit", subject=subject)

    validate_csrf(request.form.get("csrf_token", ""))

    code = (request.form.get("code") or "").strip()
    name = (request.form.get("name") or "").strip()
    credits_raw = (request.form.get("credits") or "3").strip()
    description = (request.form.get("description") or "").strip()

    if not code or not name:
        flash("Vui lòng nhập Code và Tên môn học.", "danger")
        return redirect(url_for("manager.manager_subject_edit", subject_id=subject_id))

    try:
        credits = int(credits_raw)
        if credits <= 0:
            raise ValueError()
    except Exception:
        flash("Tín chỉ phải là số nguyên dương.", "danger")
        return redirect(url_for("manager.manager_subject_edit", subject_id=subject_id))

    exist = Subject.query.filter(Subject.code == code, Subject.id != subject.id).first()
    if exist:
        flash("Code môn học đã tồn tại.", "danger")
        return redirect(url_for("manager.manager_subject_edit", subject_id=subject_id))

    subject.code = code
    subject.name = name
    subject.credits = credits
    subject.description = description or None

    db.session.commit()
    flash("Đã cập nhật môn học!", "success")
    return redirect(url_for("manager.manager_subjects"))


@manager_bp.post("/subjects/<int:subject_id>/delete")
@login_required
@roles_required("manager")
def manager_subject_delete(subject_id: int):
    subject = Subject.query.get(subject_id)
    if not subject:
        abort(404)

    validate_csrf(request.form.get("csrf_token", ""))

    db.session.delete(subject)
    db.session.commit()
    flash("Đã xoá môn học!", "success")
    return redirect(url_for("manager.manager_subjects"))


# =========================================================
# CLASSES (GV CRUD toàn quyền)
# =========================================================
@manager_bp.get("/classes")
@login_required
@roles_required("manager")
def manager_classes():
    q = (request.args.get("q") or "").strip()

    query = Class.query
    if q:
        query = query.filter(
            (Class.code.ilike(f"%{q}%")) |
            (Class.name.ilike(f"%{q}%"))
        )

    classes = query.order_by(Class.id.desc()).all()
    subjects = Subject.query.order_by(Subject.name.asc()).all()
    return render_template("manager/classes.html", classes=classes, subjects=subjects, q=q)


@manager_bp.route("/classes/new", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_class_create():
    subjects = Subject.query.order_by(Subject.name.asc()).all()

    if request.method == "GET":
        return render_template(
            "manager/class_form.html",
            mode="create",
            c=None,
            subjects=subjects,
            selected_ids=set()
        )

    validate_csrf(request.form.get("csrf_token", ""))

    code = (request.form.get("code") or "").strip()
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()

    subject_ids = request.form.getlist("subject_ids")
    subject_ids = [int(x) for x in subject_ids if str(x).isdigit()]

    if not code or not name:
        flash("Vui lòng nhập Code và Tên lớp.", "danger")
        return redirect(url_for("manager.manager_class_create"))

    if Class.query.filter_by(code=code).first():
        flash("Code lớp đã tồn tại.", "danger")
        return redirect(url_for("manager.manager_class_create"))

    c = Class(code=code, name=name, description=description or None)
    c.subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all() if subject_ids else []

    db.session.add(c)
    db.session.commit()
    flash("Đã thêm lớp!", "success")
    return redirect(url_for("manager.manager_classes"))


@manager_bp.route("/classes/<int:class_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_class_edit(class_id: int):
    c = Class.query.get(class_id)
    if not c:
        abort(404)

    subjects = Subject.query.order_by(Subject.name.asc()).all()

    if request.method == "GET":
        selected_ids = {s.id for s in c.subjects}
        return render_template(
            "manager/class_form.html",
            mode="edit",
            c=c,
            subjects=subjects,
            selected_ids=selected_ids
        )

    validate_csrf(request.form.get("csrf_token", ""))

    code = (request.form.get("code") or "").strip()
    name = (request.form.get("name") or "").strip()
    description = (request.form.get("description") or "").strip()

    subject_ids = request.form.getlist("subject_ids")
    subject_ids = [int(x) for x in subject_ids if str(x).isdigit()]

    if not code or not name:
        flash("Vui lòng nhập Code và Tên lớp.", "danger")
        return redirect(url_for("manager.manager_class_edit", class_id=class_id))

    exist = Class.query.filter(Class.code == code, Class.id != c.id).first()
    if exist:
        flash("Code lớp đã tồn tại.", "danger")
        return redirect(url_for("manager.manager_class_edit", class_id=class_id))

    c.code = code
    c.name = name
    c.description = description or None
    c.subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all() if subject_ids else []

    db.session.commit()
    flash("Đã cập nhật lớp!", "success")
    return redirect(url_for("manager.manager_classes"))


@manager_bp.post("/classes/<int:class_id>/delete")
@login_required
@roles_required("manager")
def manager_class_delete(class_id: int):
    c = Class.query.get(class_id)
    if not c:
        abort(404)

    validate_csrf(request.form.get("csrf_token", ""))

    db.session.delete(c)
    db.session.commit()
    flash("Đã xoá lớp!", "success")
    return redirect(url_for("manager.manager_classes"))


# =========================================================
# EXAMS (GV CRUD toàn quyền)
# =========================================================
@manager_bp.get("/exams")
@login_required
@roles_required("manager")
def manager_exams():
    q = (request.args.get("q") or "").strip()

    query = Exam.query.join(Subject)
    if q:
        query = query.filter(
            (Exam.name.ilike(f"%{q}%")) |
            (Subject.name.ilike(f"%{q}%")) |
            (Subject.code.ilike(f"%{q}%"))
        )

    exams = query.order_by(Exam.id.desc()).all()
    subjects = Subject.query.order_by(Subject.name.asc()).all()
    return render_template("manager/exams.html", exams=exams, subjects=subjects, q=q)


@manager_bp.route("/exams/new", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_exam_create():
    subjects = Subject.query.order_by(Subject.name.asc()).all()

    if request.method == "GET":
        return render_template("manager/exam_form.html", mode="create", e=None, subjects=subjects)

    validate_csrf(request.form.get("csrf_token", ""))

    name = (request.form.get("name") or "").strip()
    subject_id = (request.form.get("subject_id") or "").strip()
    exam_date = (request.form.get("exam_date") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not name or not subject_id.isdigit():
        flash("Vui lòng nhập Tên kỳ thi và chọn Môn học.", "danger")
        return redirect(url_for("manager.manager_exam_create"))

    subject = Subject.query.get(int(subject_id))
    if not subject:
        flash("Môn học không tồn tại.", "danger")
        return redirect(url_for("manager.manager_exam_create"))

    dt = None
    if exam_date:
        try:
            dt = datetime.strptime(exam_date, "%Y-%m-%d").date()
        except Exception:
            flash("Ngày thi không đúng định dạng (YYYY-MM-DD).", "danger")
            return redirect(url_for("manager.manager_exam_create"))

    e = Exam(name=name, subject_id=subject.id, exam_date=dt, description=description or None)
    db.session.add(e)
    db.session.commit()
    flash("Đã thêm kỳ thi!", "success")
    return redirect(url_for("manager.manager_exams"))


@manager_bp.route("/exams/<int:exam_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_exam_edit(exam_id: int):
    e = Exam.query.get(exam_id)
    if not e:
        abort(404)

    subjects = Subject.query.order_by(Subject.name.asc()).all()

    if request.method == "GET":
        return render_template("manager/exam_form.html", mode="edit", e=e, subjects=subjects)

    validate_csrf(request.form.get("csrf_token", ""))

    name = (request.form.get("name") or "").strip()
    subject_id = (request.form.get("subject_id") or "").strip()
    exam_date = (request.form.get("exam_date") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not name or not subject_id.isdigit():
        flash("Vui lòng nhập Tên kỳ thi và chọn Môn học.", "danger")
        return redirect(url_for("manager.manager_exam_edit", exam_id=exam_id))

    subject = Subject.query.get(int(subject_id))
    if not subject:
        flash("Môn học không tồn tại.", "danger")
        return redirect(url_for("manager.manager_exam_edit", exam_id=exam_id))

    dt = None
    if exam_date:
        try:
            dt = datetime.strptime(exam_date, "%Y-%m-%d").date()
        except Exception:
            flash("Ngày thi không đúng định dạng (YYYY-MM-DD).", "danger")
            return redirect(url_for("manager.manager_exam_edit", exam_id=exam_id))

    e.name = name
    e.subject_id = subject.id
    e.exam_date = dt
    e.description = description or None

    db.session.commit()
    flash("Đã cập nhật kỳ thi!", "success")
    return redirect(url_for("manager.manager_exams"))


@manager_bp.post("/exams/<int:exam_id>/delete")
@login_required
@roles_required("manager")
def manager_exam_delete(exam_id: int):
    e = Exam.query.get(exam_id)
    if not e:
        abort(404)

    validate_csrf(request.form.get("csrf_token", ""))

    db.session.delete(e)
    db.session.commit()
    flash("Đã xoá kỳ thi!", "success")
    return redirect(url_for("manager.manager_exams"))


# =========================================================
# GRADES (GV CRUD toàn quyền)
# =========================================================
@manager_bp.get("/grades")
@login_required
@roles_required("manager")
def manager_grades():
    student_q = (request.args.get("student_q") or "").strip()
    subject_id = (request.args.get("subject_id") or "").strip()
    exam_id = (request.args.get("exam_id") or "").strip()

    query = Grade.query

    if student_q:
        query = query.join(Student).filter(
            (Student.ma_sv.ilike(f"%{student_q}%")) |
            (Student.ten_sv.ilike(f"%{student_q}%")) |
            (Student.email.ilike(f"%{student_q}%"))
        )

    if subject_id.isdigit():
        query = query.filter(Grade.subject_id == int(subject_id))

    if exam_id.isdigit():
        query = query.filter(Grade.exam_id == int(exam_id))

    grades = query.order_by(Grade.id.desc()).all()
    subjects = Subject.query.order_by(Subject.id.desc()).all()
    exams = Exam.query.order_by(Exam.id.desc()).all()

    return render_template(
        "manager/grades.html",
        grades=grades,
        subjects=subjects,
        exams=exams,
        student_q=student_q,
        subject_id=subject_id,
        exam_id=exam_id,
    )


@manager_bp.route("/grades/new", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_grade_create():
    if request.method == "GET":
        students = Student.query.order_by(Student.id.desc()).all()
        subjects = Subject.query.order_by(Subject.id.desc()).all()
        exams = Exam.query.order_by(Exam.id.desc()).all()
        return render_template(
            "manager/grade_form.html",
            mode="create",
            g=None,
            students=students,
            subjects=subjects,
            exams=exams,
        )

    validate_csrf(request.form.get("csrf_token", ""))

    student_id = request.form.get("student_id", "")
    subject_id = request.form.get("subject_id", "")
    exam_id = request.form.get("exam_id", "")
    score_raw = (request.form.get("score") or "").strip()
    note = (request.form.get("note") or "").strip()

    if not (student_id.isdigit() and subject_id.isdigit() and exam_id.isdigit()):
        flash("Vui lòng chọn Sinh viên / Môn / Kỳ thi hợp lệ.", "danger")
        return redirect(url_for("manager.manager_grade_create"))

    try:
        score = float(score_raw)
    except Exception:
        flash("Điểm không hợp lệ (phải là số).", "danger")
        return redirect(url_for("manager.manager_grade_create"))

    if score < 0 or score > 10:
        flash("Điểm phải nằm trong khoảng 0 - 10.", "danger")
        return redirect(url_for("manager.manager_grade_create"))

    exists = Grade.query.filter_by(
        student_id=int(student_id),
        subject_id=int(subject_id),
        exam_id=int(exam_id),
    ).first()
    if exists:
        flash("Điểm đã tồn tại cho SV - Môn - Kỳ thi này.", "danger")
        return redirect(url_for("manager.manager_grade_create"))

    g = Grade(
        student_id=int(student_id),
        subject_id=int(subject_id),
        exam_id=int(exam_id),
        score=score,
        note=note or None,
    )
    db.session.add(g)
    db.session.commit()
    flash("Đã thêm điểm!", "success")
    return redirect(url_for("manager.manager_grades"))


@manager_bp.route("/grades/<int:grade_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_grade_edit(grade_id: int):
    g = Grade.query.get(grade_id)
    if not g:
        abort(404)

    if request.method == "GET":
        students = Student.query.order_by(Student.id.desc()).all()
        subjects = Subject.query.order_by(Subject.id.desc()).all()
        exams = Exam.query.order_by(Exam.id.desc()).all()
        return render_template(
            "manager/grade_form.html",
            mode="edit",
            g=g,
            students=students,
            subjects=subjects,
            exams=exams,
        )

    validate_csrf(request.form.get("csrf_token", ""))

    student_id = request.form.get("student_id", "")
    subject_id = request.form.get("subject_id", "")
    exam_id = request.form.get("exam_id", "")
    score_raw = (request.form.get("score") or "").strip()
    note = (request.form.get("note") or "").strip()

    if not (student_id.isdigit() and subject_id.isdigit() and exam_id.isdigit()):
        flash("Vui lòng chọn Sinh viên / Môn / Kỳ thi hợp lệ.", "danger")
        return redirect(url_for("manager.manager_grade_edit", grade_id=grade_id))

    try:
        score = float(score_raw)
    except Exception:
        flash("Điểm không hợp lệ (phải là số).", "danger")
        return redirect(url_for("manager.manager_grade_edit", grade_id=grade_id))

    if score < 0 or score > 10:
        flash("Điểm phải nằm trong khoảng 0 - 10.", "danger")
        return redirect(url_for("manager.manager_grade_edit", grade_id=grade_id))

    exists = Grade.query.filter(
        Grade.student_id == int(student_id),
        Grade.subject_id == int(subject_id),
        Grade.exam_id == int(exam_id),
        Grade.id != g.id
    ).first()
    if exists:
        flash("Bị trùng: đã có điểm cho SV - Môn - Kỳ thi này.", "danger")
        return redirect(url_for("manager.manager_grade_edit", grade_id=grade_id))

    g.student_id = int(student_id)
    g.subject_id = int(subject_id)
    g.exam_id = int(exam_id)
    g.score = score
    g.note = note or None

    db.session.commit()
    flash("Đã cập nhật điểm!", "success")
    return redirect(url_for("manager.manager_grades"))


@manager_bp.post("/grades/<int:grade_id>/delete")
@login_required
@roles_required("manager")
def manager_grade_delete(grade_id: int):
    g = Grade.query.get(grade_id)
    if not g:
        abort(404)

    validate_csrf(request.form.get("csrf_token", ""))

    db.session.delete(g)
    db.session.commit()
    flash("Đã xoá điểm!", "success")
    return redirect(url_for("manager.manager_grades"))


# =========================================================
# LESSONS (GV CRUD toàn quyền)
# =========================================================
@manager_bp.get("/lessons")
@login_required
@roles_required("manager")
def manager_lessons():
    subject_id = request.args.get("subject_id", type=int)
    subjects = Subject.query.order_by(Subject.name.asc()).all()

    q = Lesson.query
    if subject_id:
        q = q.filter(Lesson.subject_id == subject_id)

    lessons = q.order_by(Lesson.subject_id.asc(), Lesson.order_no.asc(), Lesson.id.asc()).all()

    return render_template(
        "manager/lessons.html",
        lessons=lessons,
        subjects=subjects,
        subject_id=subject_id
    )


@manager_bp.route("/lessons/new", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_lessons_create():
    subjects = Subject.query.order_by(Subject.name.asc()).all()
    if not subjects:
        flash("Chưa có môn học. Hãy tạo môn học trước!", "warning")
        return redirect(url_for("manager.manager_subjects"))

    if request.method == "GET":
        return render_template("manager/lesson_form.html", mode="create", lesson=None, subjects=subjects)

    validate_csrf(request.form.get("csrf_token", ""))

    subject_id = int(request.form.get("subject_id") or 0)
    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    video_url = (request.form.get("video_url") or "").strip()
    order_no = request.form.get("order_no", type=int) or 1

    if not subject_id or not title:
        flash("Vui lòng chọn môn và nhập tiêu đề.", "danger")
        return redirect(url_for("manager.manager_lessons_create"))

    lesson = Lesson(
        subject_id=subject_id,
        title=title,
        content=content or None,
        video_url=video_url or None,
        order_no=order_no
    )
    db.session.add(lesson)
    db.session.commit()
    flash("Đã thêm bài học!", "success")
    return redirect(url_for("manager.manager_lessons"))


@manager_bp.route("/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("manager")
def manager_lessons_edit(lesson_id: int):
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        abort(404)

    subjects = Subject.query.order_by(Subject.name.asc()).all()

    if request.method == "GET":
        return render_template("manager/lesson_form.html", mode="edit", lesson=lesson, subjects=subjects)

    validate_csrf(request.form.get("csrf_token", ""))

    lesson.subject_id = int(request.form.get("subject_id") or 0)
    lesson.title = (request.form.get("title") or "").strip()
    lesson.content = (request.form.get("content") or "").strip() or None
    lesson.video_url = (request.form.get("video_url") or "").strip() or None
    lesson.order_no = request.form.get("order_no", type=int) or 1

    if not lesson.subject_id or not lesson.title:
        flash("Vui lòng chọn môn và nhập tiêu đề.", "danger")
        return redirect(url_for("manager.manager_lessons_edit", lesson_id=lesson_id))

    db.session.commit()
    flash("Đã cập nhật bài học!", "success")
    return redirect(url_for("manager.manager_lessons"))


@manager_bp.post("/lessons/<int:lesson_id>/delete")
@login_required
@roles_required("manager")
def manager_lessons_delete(lesson_id: int):
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        abort(404)

    validate_csrf(request.form.get("csrf_token", ""))

    db.session.delete(lesson)
    db.session.commit()
    flash("Đã xoá bài học!", "success")
    return redirect(url_for("manager.manager_lessons"))
