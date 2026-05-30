import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
csrf = CSRFProtect()


def create_app(config_name: str = None):
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    from app.config import config
    env = config_name or os.getenv("FLASK_ENV", "production")
    app.config.from_object(config.get(env, config["default"]))

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # ── Blueprints ────────────────────────────────────────────────────────────
    from app.auth.routes import auth_bp
    from app.store.routes import store_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(store_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/health")
    def health():
        try:
            db.session.execute(db.text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        status = "healthy" if db_ok else "degraded"
        code = 200 if db_ok else 503
        return jsonify({"status": status, "database": db_ok}), code

    # ── JWT error handlers ────────────────────────────────────────────────────
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        from flask import redirect, url_for, request
        if request.path.startswith("/admin") or request.path.startswith("/api"):
            return jsonify({"error": "Authentication required", "reason": reason}), 401
        return redirect(url_for("auth.login"))

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(429)
    def too_many_requests(e):
        from flask import render_template
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    # ── Logging ───────────────────────────────────────────────────────────────
    if not app.debug:
        os.makedirs("/var/log/ecommerce", exist_ok=True)
        handler = RotatingFileHandler(
            "/var/log/ecommerce/app.log", maxBytes=10_000_000, backupCount=5
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s – %(message)s")
        )
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    # ── Seed data ─────────────────────────────────────────────────────────────
    with app.app_context():
        _seed_defaults(app)

    return app


def _seed_defaults(app):
    """Create default admin and product categories on first run."""
    from app.models import User, Category

    try:
        # categories
        default_categories = [
            ("Electronics", "electronics"),
            ("Clothing", "clothing"),
            ("Books", "books"),
            ("Home & Kitchen", "home-kitchen"),
            ("Sports", "sports"),
        ]
        for name, slug in default_categories:
            if not Category.query.filter_by(slug=slug).first():
                db.session.add(Category(name=name, slug=slug))

        # default admin
        if not User.query.filter_by(role="admin").first():
            admin_pw = bcrypt.generate_password_hash("Admin@123456").decode("utf-8")
            db.session.add(
                User(
                    email="admin@store.com",
                    name="Store Admin",
                    password_hash=admin_pw,
                    role="admin",
                )
            )

        db.session.commit()
    except Exception:
        db.session.rollback()
