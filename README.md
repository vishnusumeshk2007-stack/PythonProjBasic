# College Achievement & Certificate Showcase Portal

A web portal where students upload achievement certificates, an admin verifies
them, and verified achievements appear on a public showcase and on each
student's profile page.

**Stack:** Flask, Flask-SQLAlchemy, Flask-Login, SQLite, Bootstrap 5, vanilla JS.

## Features

- Student registration & login
- Upload certificates (PDF / JPG / PNG) with title, category, issuer, date, description
- Personal dashboard with status tracking (Pending / Verified / Rejected)
- Admin panel to verify or reject submissions, with a remark
- Public showcase homepage: search + filter by category, only shows Verified items
- Individual student public profile pages (shareable, e.g. for a resume link)
- Certificate detail page with the uploaded file viewable inline

## Project structure

```
cert_portal/
├── app.py                # routes, app config, seeding
├── models.py              # User & Certificate SQLAlchemy models
├── requirements.txt
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── uploads/           # uploaded certificate files land here
└── templates/
    ├── base.html, index.html, login.html, register.html
    ├── dashboard.html, add_certificate.html, view_certificate.html
    ├── profile.html, admin.html
```

## Setup

```bash
cd cert_portal
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The app runs at `http://127.0.0.1:5000`. The database (`portal.db`) and
tables are created automatically on first run.

### Demo admin account

A default admin account is auto-seeded on first run so you can test
verification immediately:

- **Email:** `admin@college.edu`
- **Password:** `admin123`

To create additional admin accounts, use the CLI helper:

```bash
flask create-admin
```

(Change the default admin password before deploying anywhere public.)

## Switching to MySQL

Swap the SQLite URI in `app.py` for a MySQL one and install a driver:

```bash
pip install pymysql
```

```python
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://user:password@localhost/cert_portal"
```

Then run `python app.py` once — `db.create_all()` will create the tables in MySQL.

## Notes / possible extensions

- Add email notifications when a certificate is verified/rejected
- Add pagination on the showcase page for large datasets
- Add a "leaderboard" of most-achieved students per department
- Export a student's verified achievements as a PDF resume addendum
