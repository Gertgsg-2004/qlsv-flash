from flask_login import UserMixin
from extensions import db, bcrypt
from datetime import datetime


# =========================================================
# Bảng phụ: giáo viên (Student role=manager) <-> lớp (Class)
# =========================================================
teacher_classes = db.Table(
    "teacher_classes",
    db.Column(
        "teacher_id",
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "class_id",
        db.Integer,
        db.ForeignKey("classes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# =========================================================
# Bảng phụ: Class <-> Subject
# =========================================================
class_subject = db.Table(
    "class_subject",
    db.Column(
        "class_id",
        db.Integer,
        db.ForeignKey("classes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "subject_id",
        db.Integer,
        db.ForeignKey("subjects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# =========================================================
# Student
# =========================================================
class Student(UserMixin, db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    ma_sv = db.Column(db.String(50), unique=True, nullable=False, index=True)
    ten_sv = db.Column(db.String(255), nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    mat_khau = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="student", index=True)
    avatar = db.Column(db.String(255), nullable=True)
    gioi_tinh = db.Column(db.String(10), nullable=True)
    dia_chi = db.Column(db.Text, nullable=True)

    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    last_failed_at = db.Column(db.DateTime, nullable=True)
    lock_until = db.Column(db.DateTime, nullable=True)

    # =========================
    # SV thuộc 1 lớp (có thể NULL)
    # =========================
    class_id = db.Column(
        db.Integer,
        db.ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    class_ = db.relationship("Class", back_populates="students")

    # =========================
    # GV (role=manager) được gán nhiều lớp
    # =========================
    teaching_classes = db.relationship(
        "Class",
        secondary=teacher_classes,
        back_populates="teachers",
        lazy="subquery",
    )

    def get_id(self):
        return str(self.id)

    def check_password(self, plain: str) -> bool:
        return bcrypt.check_password_hash(self.mat_khau, plain)

    def __repr__(self):
        return f"<Student id={self.id} ma_sv={self.ma_sv} role={self.role}>"

# =========================================================
# Subject
# =========================================================
class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    credits = db.Column(db.Integer, nullable=False, default=3)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Subject {self.code} - {self.name}>"

# =========================================================
# Class
# =========================================================
class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # many-to-many với Subject
    subjects = db.relationship(
        "Subject",
        secondary=class_subject,
        backref=db.backref("classes", lazy="dynamic"),
        lazy="subquery",
    )

    # 1 lớp có nhiều SV
    students = db.relationship(
        "Student",
        back_populates="class_",
        lazy="dynamic",
    )

    # 1 lớp có nhiều GV phụ trách
    teachers = db.relationship(
        "Student",
        secondary=teacher_classes,
        back_populates="teaching_classes",
        lazy="subquery",
    )

    def __repr__(self):
        return f"<Class {self.code} - {self.name}>"

# =========================================================
# Exam
# =========================================================
class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(255), nullable=False, index=True)
    exam_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject = db.relationship("Subject", backref=db.backref("exams", lazy=True))

    def __repr__(self):
        return f"<Exam {self.name} subject_id={self.subject_id}>"

# =========================================================
# Grade
# =========================================================
class Grade(db.Model):
    __tablename__ = "grades"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    score = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("student_id", "subject_id", "exam_id", name="uq_grade"),
    )

    student = db.relationship("Student", backref=db.backref("grades", lazy=True))
    subject = db.relationship("Subject", backref=db.backref("grades", lazy=True))
    exam = db.relationship("Exam", backref=db.backref("grades", lazy=True))

    def __repr__(self):
        return f"<Grade id={self.id} student_id={self.student_id} score={self.score}>"

# =========================================================
# Lesson
# =========================================================
class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    order_no = db.Column(db.Integer, nullable=False, default=1)

    subject = db.relationship("Subject", backref=db.backref("lessons", lazy=True))

    def __repr__(self):
        return f"<Lesson id={self.id} subject_id={self.subject_id} title={self.title}>"
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    # ai nhận thông báo
    user_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)

    # link để bấm chuyển trang (tuỳ chọn)
    link = db.Column(db.String(255), nullable=True)

    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # quan hệ
    user = db.relationship("Student", backref=db.backref("notifications", lazy=True))
