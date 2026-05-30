import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    # ── Core ──────────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    WTF_CSRF_ENABLED = True

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/ecommerce_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 280
    SQLALCHEMY_POOL_TIMEOUT = 20
    SQLALCHEMY_POOL_PRE_PING = True

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-change-in-prod")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = True          # HTTPS only in prod
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    # CSRF for authenticated POSTs is handled by Flask-WTF (the `csrf_token`
    # field present in every form) together with SameSite=Lax cookies. JWT's
    # own header-based double-submit is left off so HTML form posts (add to
    # cart, checkout, etc.) aren't rejected for a missing X-CSRF-TOKEN header.
    JWT_COOKIE_CSRF_PROTECT = False

    # ── AWS / S3 ──────────────────────────────────────────────────────────────
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN", "")

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"

    # ── Upload ────────────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # ── Pagination ────────────────────────────────────────────────────────────
    PRODUCTS_PER_PAGE = 12


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    JWT_COOKIE_SECURE = False        # Allow HTTP in dev
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/ecommerce_db",
    )


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    JWT_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
