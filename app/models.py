from datetime import datetime, timezone
from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("customer", "admin"), default="customer", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # relationships
    cart_items = db.relationship("Cart", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.email}>"

    def is_admin(self):
        return self.role == "admin"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)

    products = db.relationship("Product", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    image_key = db.Column(db.String(512), nullable=True)   # S3 object key
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    cart_items = db.relationship("Cart", backref="product", lazy="dynamic")
    order_items = db.relationship("OrderItem", backref="product", lazy="dynamic")

    def __repr__(self):
        return f"<Product {self.name}>"

    @property
    def image_url(self):
        from flask import current_app
        if not self.image_key:
            return "/static/img/placeholder.png"
        # Locally bundled image (seeded demo data / dev without S3).
        # Stored as "local/<path>" and served straight from /static/img/.
        if self.image_key.startswith("local/"):
            return f"/static/img/{self.image_key[len('local/'):]}"
        cf = current_app.config.get("CLOUDFRONT_DOMAIN")
        bucket = current_app.config.get("S3_BUCKET")
        if cf:
            return f"https://{cf}/{self.image_key}"
        if bucket:
            region = current_app.config.get("AWS_REGION", "ap-south-1")
            return f"https://{bucket}.s3.{region}.amazonaws.com/{self.image_key}"
        return "/static/img/placeholder.png"

    @property
    def in_stock(self):
        return self.stock > 0


class Cart(db.Model):
    __tablename__ = "cart"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "product_id"),)

    @property
    def subtotal(self):
        return self.quantity * float(self.product.price)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.Enum("pending", "confirmed", "shipped", "delivered", "cancelled"),
        default="pending",
        nullable=False,
    )
    shipping_name = db.Column(db.String(100), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_city = db.Column(db.String(80), nullable=False)
    shipping_pincode = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items = db.relationship("OrderItem", backref="order", lazy="subquery", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order #{self.id} {self.status}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)   # price at time of purchase

    @property
    def subtotal(self):
        return self.quantity * float(self.unit_price)
