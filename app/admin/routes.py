import logging

from flask import flash, redirect, render_template, request, url_for

from app import db
from app.admin import admin_bp
from app.models import Category, Order, Product, User
from app.utils import admin_required, current_user, delete_product_image, sanitize, upload_product_image

logger = logging.getLogger(__name__)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route("/")
@admin_required
def dashboard():
    user = current_user()
    stats = {
        "total_users":    User.query.filter_by(role="customer").count(),
        "total_products": Product.query.filter_by(is_active=True).count(),
        "total_orders":   Order.query.count(),
        "total_revenue":  db.session.query(db.func.sum(Order.total_amount))
                            .filter(Order.status != "cancelled").scalar() or 0,
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    low_stock = Product.query.filter(Product.stock < 5, Product.is_active == True).all()
    return render_template(
        "admin/dashboard.html",
        user=user, stats=stats,
        recent_orders=recent_orders,
        low_stock=low_stock,
    )


# ── Products ──────────────────────────────────────────────────────────────────

@admin_bp.route("/products")
@admin_required
def products():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    q = sanitize(request.args.get("q", "").strip())
    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template(
        "admin/products.html",
        user=user, products=pagination.items,
        pagination=pagination, search_query=q,
    )


@admin_bp.route("/products/new", methods=["GET", "POST"])
@admin_required
def product_new():
    user = current_user()
    categories = Category.query.all()

    if request.method == "POST":
        name = sanitize(request.form.get("name", "").strip())
        description = sanitize(request.form.get("description", "").strip())
        price_str = request.form.get("price", "0")
        stock_str = request.form.get("stock", "0")
        category_id = request.form.get("category_id", type=int)
        image_file = request.files.get("image")

        errors = []
        if not name:
            errors.append("Product name is required.")
        try:
            price = float(price_str)
            if price < 0:
                raise ValueError
        except ValueError:
            errors.append("Invalid price.")
            price = 0.0
        try:
            stock = int(stock_str)
            if stock < 0:
                raise ValueError
        except ValueError:
            errors.append("Invalid stock number.")
            stock = 0

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("admin/product_form.html", user=user, categories=categories, action="new")

        image_key = upload_product_image(image_file) if image_file else None
        product = Product(
            name=name, description=description,
            price=price, stock=stock,
            category_id=category_id, image_key=image_key,
        )
        db.session.add(product)
        db.session.commit()
        logger.info("PRODUCT_CREATED id=%s name=%s", product.id, name)
        flash(f"Product '{name}' created.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", user=user, categories=categories, action="new")


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id):
    user = current_user()
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == "POST":
        product.name = sanitize(request.form.get("name", "").strip())
        product.description = sanitize(request.form.get("description", "").strip())
        try:
            product.price = float(request.form.get("price", 0))
        except ValueError:
            product.price = product.price
        try:
            product.stock = int(request.form.get("stock", 0))
        except ValueError:
            pass
        product.category_id = request.form.get("category_id", type=int)
        product.is_active = "is_active" in request.form

        image_file = request.files.get("image")
        if image_file and image_file.filename:
            new_key = upload_product_image(image_file)
            if new_key:
                if product.image_key:
                    delete_product_image(product.image_key)
                product.image_key = new_key

        db.session.commit()
        logger.info("PRODUCT_UPDATED id=%s", product_id)
        flash("Product updated.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", user=user, product=product, categories=categories, action="edit")


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = False   # soft delete
    db.session.commit()
    logger.info("PRODUCT_DELETED id=%s", product_id)
    flash(f"Product '{product.name}' removed.", "warning")
    return redirect(url_for("admin.products"))


# ── Orders ────────────────────────────────────────────────────────────────────

@admin_bp.route("/orders")
@admin_required
def orders():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template(
        "admin/orders.html",
        user=user, orders=pagination.items,
        pagination=pagination, current_status=status,
    )


@admin_bp.route("/orders/<int:order_id>")
@admin_required
def order_detail(order_id):
    user = current_user()
    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", user=user, order=order)


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    allowed = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
    if new_status in allowed:
        order.status = new_status
        db.session.commit()
        logger.info("ORDER_STATUS_CHANGED order_id=%s status=%s", order_id, new_status)
        flash(f"Order #{order_id} status updated to '{new_status}'.", "success")
    else:
        flash("Invalid status.", "danger")
    return redirect(url_for("admin.order_detail", order_id=order_id))


# ── Users ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/users")
@admin_required
def users():
    user = current_user()
    page = request.args.get("page", 1, type=int)
    pagination = (
        User.query.filter_by(role="customer")
        .order_by(User.created_at.desc())
        .paginate(page=page, per_page=25, error_out=False)
    )
    return render_template("admin/users.html", user=user, customers=pagination.items, pagination=pagination)


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def user_toggle(user_id):
    target = User.query.get_or_404(user_id)
    target.is_active = not target.is_active
    db.session.commit()
    state = "enabled" if target.is_active else "disabled"
    flash(f"User '{target.email}' has been {state}.", "info")
    return redirect(url_for("admin.users"))
