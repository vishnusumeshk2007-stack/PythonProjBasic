from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

CATEGORIES = ["Technical", "Sports", "Cultural", "Academic", "Internship", "Other"]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # student | admin
    department = db.Column(db.String(120))
    roll_no = db.Column(db.String(50))
    bio = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    certificates = db.relationship(
        "Certificate", backref="owner", cascade="all, delete-orphan", lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def verified_count(self):
        return sum(1 for c in self.certificates if c.status == "Verified")


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, default="Other")
    issuer = db.Column(db.String(150))
    issue_date = db.Column(db.Date)
    file_path = db.Column(db.String(300))  # stored filename
    status = db.Column(db.String(20), nullable=False, default="Pending")  # Pending|Verified|Rejected
    admin_remark = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
