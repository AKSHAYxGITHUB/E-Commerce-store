import logging
import os
import uuid
from functools import wraps

import bleach
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from flask import abort, current_app, redirect, url_for
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from PIL import Image
import io

logger = logging.getLogger(__name__)

# ── Allowed HTML tags for user content ────────────────────────────────────────
ALLOWED_TAGS = ["b", "i", "u", "em", "strong"]
ALLOWED_ATTRS: dict = {}


def sanitize(text: str) -> str:
    """Strip dangerous HTML from user-supplied strings."""
    if not text:
        return ""
    return bleach.clean(str(text), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


# ── Auth decorators ───────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(locations=["cookies"])
        except Exception:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(locations=["cookies"])
            claims = get_jwt()
            if claims.get("role") != "admin":
                abort(403)
        except Exception:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def current_user():
    """Return the User object for the JWT identity, or None."""
    try:
        verify_jwt_in_request(locations=["cookies"])
        uid = get_jwt_identity()
        if uid:
            from app.models import User
            return User.query.get(uid)
    except Exception:
        pass
    return None


# ── S3 helpers ────────────────────────────────────────────────────────────────

def _s3_client():
    return boto3.client(
        "s3",
        region_name=current_app.config["AWS_REGION"],
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", set())


def upload_product_image(file_obj) -> str | None:
    """
    Resize the image to max 800×800, convert to JPEG and upload to S3.
    Returns the S3 object key, or None on failure.
    """
    if not file_obj or file_obj.filename == "":
        return None
    if not allowed_file(file_obj.filename):
        return None

    bucket = current_app.config.get("S3_BUCKET")
    if not bucket:
        logger.warning("S3_BUCKET not configured – skipping upload")
        return None

    try:
        img = Image.open(file_obj.stream)
        img.thumbnail((800, 800), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        buf.seek(0)

        key = f"products/{uuid.uuid4().hex}.jpg"
        _s3_client().upload_fileobj(
            buf,
            bucket,
            key,
            ExtraArgs={"ContentType": "image/jpeg", "CacheControl": "max-age=86400"},
        )
        logger.info("Uploaded product image to S3: %s", key)
        return key
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 upload failed: %s", exc)
        return None
    except Exception as exc:
        logger.error("Image processing failed: %s", exc)
        return None


def delete_product_image(image_key: str) -> None:
    """Delete an image from S3 by key."""
    bucket = current_app.config.get("S3_BUCKET")
    if not bucket or not image_key:
        return
    try:
        _s3_client().delete_object(Bucket=bucket, Key=image_key)
        logger.info("Deleted S3 image: %s", image_key)
    except Exception as exc:
        logger.error("Failed to delete S3 image %s: %s", image_key, exc)
