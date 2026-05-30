import logging

from flask import flash, redirect, render_template, request, url_for

from app import db, limiter
from app.models import Cart, Category, Order, OrderItem, Product
from app.store import store_bp
from app.utils import current_user, login_required, sanitize

logger = logging.getLogger(__name__)


# ── Homepage ──────────────────────────────────────────────────────────────────

@store_bp.route("/")
def index():
    featured = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    categories = Category.query.all()
    user = current_user()
    return render_template("store/index.html", featured=featured, categories=categories, user=user)


# ── Product list ──────────────────────────────────────────────────────────────

@store_bp.route("/products")
def products():
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("category", "")
    q = sanitize(request.args.get("q", "").strip())

    query = Product.query.filter_by(is_active=True)
    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    from flask import current_app
    per_page = current_app.config.get("PRODUCTS_PER_PAGE", 12)
    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    categories = Category.query.all()
    user = current_user()
    return render_template(
        "store/products.html",
        pagination=pagination,
        products=pagination.items,
        categories=categories,
        current_category=category_slug,
        search_query=q,
        user=user,
    )


# ── Product detail ────────────────────────────────────────────────────────────

@store_bp.route("/products/<int:product_id>")
def product_detail(product_id):
    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()
    related = (
        Product.query.filter_by(category_id=product.category_id, is_active=True)
        .filter(Product.id != product.id)
        .limit(4)
        .all()
    )
    user = current_user()
    return render_template("store/product_detail.html", product=product, related=related, user=user)


# ── Cart ──────────────────────────────────────────────────────────────────────

@store_bp.route("/cart")
@login_required
def cart():
    user = current_user()
    items = Cart.query.filter_by(user_id=user.id).all()
    total = sum(i.subtotal for i in items)
    return render_template("store/cart.html", items=items, total=total, user=user)


@store_bp.route("/cart/add", methods=["POST"])
@login_required
@limiter.limit("60 per minute")
def cart_add():
    user = current_user()
    product_id = request.form.get("product_id", type=int)
    qty = request.form.get("quantity", 1, type=int)

    if not product_id or qty < 1:
        flash("Invalid request.", "danger")
        return redirect(request.referrer or url_for("store.index"))

    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()
    if product.stock < qty:
        flash("Not enough stock available.", "warning")
        return redirect(url_for("store.product_detail", product_id=product_id))

    item = Cart.query.filter_by(user_id=user.id, product_id=product_id).first()
    if item:
        new_qty = item.quantity + qty
        if new_qty > product.stock:
            flash("Cannot add more — stock limit reached.", "warning")
        else:
            item.quantity = new_qty
            db.session.commit()
            flash(f"Updated cart: {product.name}", "success")
    else:
        db.session.add(Cart(user_id=user.id, product_id=product_id, quantity=qty))
        db.session.commit()
        flash(f"Added to cart: {product.name}", "success")

    return redirect(request.referrer or url_for("store.cart"))


@store_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def cart_remove(item_id):
    user = current_user()
    item = Cart.query.filter_by(id=item_id, user_id=user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "info")
    return redirect(url_for("store.cart"))


@store_bp.route("/cart/update", methods=["POST"])
@login_required
def cart_update():
    user = current_user()
    item_id = request.form.get("item_id", type=int)
    qty = request.form.get("quantity", type=int)

    if not item_id or not qty:
        return redirect(url_for("store.cart"))

    item = Cart.query.filter_by(id=item_id, user_id=user.id).first_or_404()
    if qty < 1:
        db.session.delete(item)
    elif qty > item.product.stock:
        flash("Not enough stock.", "warning")
    else:
        item.quantity = qty
    db.session.commit()
    return redirect(url_for("store.cart"))


# ── Checkout ──────────────────────────────────────────────────────────────────

@store_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per hour")
def checkout():
    user = current_user()
    items = Cart.query.filter_by(user_id=user.id).all()
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("store.cart"))

    if request.method == "POST":
        ship_name = sanitize(request.form.get("shipping_name", "").strip())
        ship_addr = sanitize(request.form.get("shipping_address", "").strip())
        ship_city = sanitize(request.form.get("shipping_city", "").strip())
        ship_pin = sanitize(request.form.get("shipping_pincode", "").strip())

        if not all([ship_name, ship_addr, ship_city, ship_pin]):
            flash("All shipping fields are required.", "danger")
            total = sum(i.subtotal for i in items)
            return render_template("store/checkout.html", items=items, total=total, user=user)

        # verify stock & calculate total
        total = 0.0
        for item in items:
            if item.product.stock < item.quantity:
                flash(f"'{item.product.name}' is out of stock.", "danger")
                return redirect(url_for("store.cart"))
            total += item.subtotal

        order = Order(
            user_id=user.id,
            total_amount=round(total, 2),
            shipping_name=ship_name,
            shipping_address=ship_addr,
            shipping_city=ship_city,
            shipping_pincode=ship_pin,
        )
        db.session.add(order)
        db.session.flush()   # get order.id before committing

        for item in items:
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                )
            )
            item.product.stock -= item.quantity
            db.session.delete(item)

        db.session.commit()
        logger.info("ORDER_PLACED order_id=%s user_id=%s total=%.2f", order.id, user.id, float(total))
        flash(f"Order #{order.id} placed successfully!", "success")
        return redirect(url_for("store.order_detail", order_id=order.id))

    total = sum(i.subtotal for i in items)
    return render_template("store/checkout.html", items=items, total=total, user=user)


# ── Orders ────────────────────────────────────────────────────────────────────

@store_bp.route("/orders")
@login_required
def orders():
    user = current_user()
    my_orders = (
        Order.query.filter_by(user_id=user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("store/orders.html", orders=my_orders, user=user)


@store_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    user = current_user()
    order = Order.query.filter_by(id=order_id, user_id=user.id).first_or_404()
    return render_template("store/order_detail.html", order=order, user=user)
