import logging
import re

from flask import flash, redirect, render_template, request, url_for
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from app import bcrypt, db, limiter
from app.auth import auth_bp
from app.models import User
from app.utils import current_user, sanitize

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PW_MIN = 8


def _validate_password(pw: str) -> list[str]:
    errors = []
    if len(pw) < PW_MIN:
        errors.append(f"Password must be at least {PW_MIN} characters.")
    if not re.search(r"[A-Z]", pw):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", pw):
        errors.append("Password must contain at least one number.")
    return errors


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user():
        return redirect(url_for("store.index"))

    if request.method == "POST":
        name = sanitize(request.form.get("name", "").strip())
        email = sanitize(request.form.get("email", "").strip().lower())
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not name or len(name) < 2:
            errors.append("Name must be at least 2 characters.")
        if not EMAIL_RE.match(email):
            errors.append("Enter a valid email address.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        errors.extend(_validate_password(password))
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html", name=name, email=email)

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(email=email, name=name, password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        logger.info("New user registered: %s", email)
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per hour; 5 per minute")
def login():
    if current_user():
        return redirect(url_for("store.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            logger.warning("FAILED_LOGIN email=%s ip=%s", email, request.remote_addr)
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        if not user.is_active:
            flash("Your account has been disabled. Contact support.", "warning")
            return render_template("auth/login.html", email=email)

        additional_claims = {"role": user.role, "name": user.name}
        access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=user.id)

        next_page = request.args.get("next")
        if user.is_admin():
            dest = next_page or url_for("admin.dashboard")
        else:
            dest = next_page or url_for("store.index")

        response = redirect(dest)
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        logger.info("LOGIN user_id=%s email=%s", user.id, email)
        return response

    return render_template("auth/login.html")


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = redirect(url_for("auth.login"))
    unset_jwt_cookies(response)
    flash("You have been logged out.", "info")
    return response


# ── Profile ───────────────────────────────────────────────────────────────────

@auth_bp.route("/profile")
def profile():
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))
    return render_template("auth/profile.html", user=user)
