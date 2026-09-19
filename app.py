import os
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for, flash, request, abort, send_from_directory
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename

from models import db, User, Certificate, CATEGORIES

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "portal.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# ---------- Public routes ----------

@app.route("/")
def index():
    query = Certificate.query.filter_by(status="Verified")

    category = request.args.get("category", "")
    search = request.args.get("q", "")

    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Certificate.title.ilike(f"%{search}%"))

    certificates = query.order_by(Certificate.created_at.desc()).limit(60).all()
    stats = {
        "students": User.query.filter_by(role="student").count(),
        "verified": Certificate.query.filter_by(status="Verified").count(),
        "total": Certificate.query.count(),
    }
    return render_template(
        "index.html",
        certificates=certificates,
        categories=CATEGORIES,
        selected_category=category,
        search=search,
        stats=stats,
    )


@app.route("/profile/<int:user_id>")
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    certs = [c for c in user.certificates if c.status == "Verified"]
    certs.sort(key=lambda c: c.created_at, reverse=True)
    return render_template("profile.html", profile_user=user, certificates=certs)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ---------- Auth ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()
        roll_no = request.form.get("roll_no", "").strip()

        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("register"))

        user = User(name=name, email=email, department=department, roll_no=roll_no)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Welcome! Your account has been created.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ---------- Student dashboard ----------

@app.route("/dashboard")
@login_required
def dashboard():
    certs = Certificate.query.filter_by(user_id=current_user.id).order_by(
        Certificate.created_at.desc()
    ).all()
    counts = {
        "total": len(certs),
        "verified": sum(1 for c in certs if c.status == "Verified"),
        "pending": sum(1 for c in certs if c.status == "Pending"),
        "rejected": sum(1 for c in certs if c.status == "Rejected"),
    }
    return render_template("dashboard.html", certificates=certs, counts=counts)


@app.route("/certificate/add", methods=["GET", "POST"])
@login_required
def add_certificate():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "Other")
        issuer = request.form.get("issuer", "").strip()
        issue_date_str = request.form.get("issue_date", "")
        file = request.files.get("file")

        if not title:
            flash("Title is required.", "danger")
            return redirect(url_for("add_certificate"))

        issue_date = None
        if issue_date_str:
            try:
                issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d").date()
            except ValueError:
                issue_date = None

        filename = None
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Only PNG, JPG and PDF files are allowed.", "danger")
                return redirect(url_for("add_certificate"))
            safe_name = secure_filename(file.filename)
            filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{safe_name}"
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        cert = Certificate(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            issuer=issuer,
            issue_date=issue_date,
            file_path=filename,
            status="Pending",
        )
        db.session.add(cert)
        db.session.commit()
        flash("Certificate submitted for verification.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_certificate.html", categories=CATEGORIES, today=date.today().isoformat())


@app.route("/certificate/<int:cert_id>/delete", methods=["POST"])
@login_required
def delete_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    if cert.user_id != current_user.id and current_user.role != "admin":
        abort(403)
    if cert.file_path:
        path = os.path.join(app.config["UPLOAD_FOLDER"], cert.file_path)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(cert)
    db.session.commit()
    flash("Certificate deleted.", "info")
    return redirect(url_for("dashboard"))


@app.route("/certificate/<int:cert_id>")
def view_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    if cert.status != "Verified" and (
        not current_user.is_authenticated
        or (current_user.id != cert.user_id and current_user.role != "admin")
    ):
        abort(403)
    return render_template("view_certificate.html", cert=cert)


# ---------- Admin ----------

@app.route("/admin")
@admin_required
def admin_dashboard():
    status_filter = request.args.get("status", "Pending")
    query = Certificate.query
    if status_filter != "All":
        query = query.filter_by(status=status_filter)
    certs = query.order_by(Certificate.created_at.desc()).all()
    counts = {
        "Pending": Certificate.query.filter_by(status="Pending").count(),
        "Verified": Certificate.query.filter_by(status="Verified").count(),
        "Rejected": Certificate.query.filter_by(status="Rejected").count(),
    }
    return render_template(
        "admin.html", certificates=certs, counts=counts, status_filter=status_filter
    )


@app.route("/admin/certificate/<int:cert_id>/<action>", methods=["POST"])
@admin_required
def admin_action(cert_id, action):
    cert = Certificate.query.get_or_404(cert_id)
    remark = request.form.get("remark", "").strip()

    if action == "verify":
        cert.status = "Verified"
        cert.admin_remark = remark
        flash(f'"{cert.title}" marked as Verified.', "success")
    elif action == "reject":
        cert.status = "Rejected"
        cert.admin_remark = remark
        flash(f'"{cert.title}" marked as Rejected.', "warning")
    elif action == "pending":
        cert.status = "Pending"
        cert.admin_remark = remark
        flash(f'"{cert.title}" reset to Pending.', "info")
    else:
        abort(400)

    db.session.commit()
    return redirect(url_for("admin_dashboard", status=request.args.get("status", "Pending")))


# ---------- CLI helper to seed an admin account ----------

@app.cli.command("create-admin")
def create_admin():
    """Usage: flask create-admin"""
    import getpass
    name = input("Admin name: ")
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password: ")
    if User.query.filter_by(email=email).first():
        print("A user with that email already exists.")
        return
    admin = User(name=name, email=email, role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Admin account created for {email}.")


DEFAULT_ADMIN_EMAIL = "admin" + "@" + "college.edu"
DEFAULT_ADMIN_PASSWORD = "admin123"

with app.app_context():
    db.create_all()
    # Seed a default admin account for convenience if none exists
    if not User.query.filter_by(role="admin").first():
        default_admin = User(
            name="Portal Admin",
            email=DEFAULT_ADMIN_EMAIL,
            role="admin",
            department="Administration",
        )
        default_admin.set_password(DEFAULT_ADMIN_PASSWORD)
        db.session.add(default_admin)
        db.session.commit()


if __name__ == "__main__":
    app.run(debug=True)
