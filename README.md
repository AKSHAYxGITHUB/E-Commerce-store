# ShopSecure – Cloud-Based E-Commerce DevSecOps Project

![Flask](https://img.shields.io/badge/Flask-3.0-green)
![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20RDS%20%7C%20S3-orange)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Jenkins](https://img.shields.io/badge/CI%2FCD-Jenkins-red)

> Cloud-based secure e-commerce web application built with DevSecOps best practices on AWS.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Application | Python 3.11 / Flask |
| Database | MySQL 8.0 (AWS RDS) |
| Web Server | Nginx (reverse proxy) |
| Container | Docker + Docker Compose |
| CI/CD | Jenkins |
| Cloud | AWS EC2, RDS, S3, CloudFront, ALB, Route 53 |
| Monitoring | AWS CloudWatch |
| Security | bcrypt, JWT, Flask-Limiter, Fail2ban, WAF |

---

## Application Workflow

### Customer journey

```
Browse store ──▶ Register / Login ──▶ Add to cart ──▶ Checkout ──▶ Order placed ──▶ Track orders
   (public)        (JWT cookie)        (cart badge)    (shipping)   (stock ↓)        (My Orders)
```

1. A visitor browses the **home page**, **product list** and **product details** (public, no login).
2. They **register** and **log in** — the app issues a signed **JWT** stored in an HTTP-only cookie.
3. Logged-in users **add products to the cart** (the navbar shows a live item-count badge), update quantities or remove items.
4. At **checkout** they enter shipping details; an **Order** + **OrderItems** are created, product stock is decremented, and the cart is cleared — all in one DB transaction.
5. Users review past purchases under **My Orders**.

### Admin journey

```
Login (admin) ──▶ Dashboard (stats) ──▶ Manage Products / Orders / Users
                                          (CRUD, image upload, status, enable/disable)
```

- **Dashboard** — totals for users, products, orders, revenue, plus recent orders and low-stock alerts.
- **Products** — create/edit/delete (soft delete); images are resized and uploaded to **S3**.
- **Orders** — view details and update status (`pending → confirmed → shipped → delivered / cancelled`).
- **Users** — enable/disable customer accounts.

### Request lifecycle (production)

```
Browser
  │  HTTPS (TLS via ACM)
  ▼
Route 53 ──▶ ALB + AWS WAF ──▶ Nginx (reverse proxy, security headers, rate limit)
                                   │
                                   ▼
                            Gunicorn → Flask app  (Docker container on EC2, private subnet)
                                   │
                ┌──────────────────┼─────────────────────┐
                ▼                  ▼                     ▼
          MySQL (RDS)       S3 + CloudFront         CloudWatch
        (data, orders)     (product images)        (logs/metrics)
```

### CI/CD flow

```
git push ──▶ Jenkins ──▶ Build Docker image ──▶ Run pytest ──▶ Trivy security scan ──▶ Deploy to EC2
```

---

## Project Structure

```
ecommerce-devsecops/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration classes
│   ├── models.py            # SQLAlchemy models
│   ├── utils.py             # S3 upload, sanitization, decorators
│   ├── auth/routes.py       # Register, login, logout
│   ├── store/routes.py      # Products, cart, checkout, orders
│   ├── admin/routes.py      # Admin dashboard + CRUD
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, images
│       └── img/products/    # Bundled demo product images (SVG)
├── docker/Dockerfile        # Production Docker image
├── docker-compose.yml       # Local dev stack
├── config/nginx.conf        # Nginx reverse proxy + security headers
├── jenkins/Jenkinsfile      # CI/CD pipeline
├── scripts/
│   ├── seed_data.py         # Seed admin + sample products/categories
│   ├── generate_images.py   # Generate local product images (SVG)
│   ├── backup.sh            # Automated DB + S3 backup
│   └── setup_server.sh      # EC2 server setup script
├── tests/                   # Pytest tests
├── requirements.txt
└── .env.example
```

---

## Repository Files — Detailed Reference

### Application core (`app/`)

| File | Responsibility |
|------|----------------|
| `app/__init__.py` | **App factory** (`create_app`). Initialises SQLAlchemy, Migrate, JWT, Bcrypt, Flask-Limiter and CSRF; registers the `auth`, `store`, `admin` blueprints; defines the `/health` check, JWT/error handlers, file logging, the **cart-count** template global, and seeds a default admin + categories on first run. |
| `app/config.py` | Configuration classes — `BaseConfig`, `Development`, `Production`, `Testing`. Holds DB URI, JWT/cookie settings, S3/CloudFront, rate-limit, upload and pagination settings. Switched via `FLASK_ENV`. |
| `app/models.py` | SQLAlchemy models: **User, Category, Product, Cart, Order, OrderItem**, including the `Product.image_url` property (local / S3 / CloudFront) and `subtotal` helpers. |
| `app/utils.py` | Shared helpers — input `sanitize()` (bleach), `login_required` / `admin_required` decorators, `current_user()`, and S3 image upload/delete with Pillow resizing. |

### Blueprints (routes)

| File | Responsibility |
|------|----------------|
| `app/auth/routes.py` | Register, login, logout, profile. Validates input, hashes passwords with bcrypt, issues JWT cookies. |
| `app/store/routes.py` | Storefront — home, product list/search, product detail, cart add/update/remove, checkout, order history. |
| `app/admin/routes.py` | Admin panel — dashboard stats, product CRUD (+ image upload), order status updates, user enable/disable. Protected by `@admin_required`. |

### Templates (`app/templates/`)

| Path | Purpose |
|------|---------|
| `base.html` | Master layout: navbar (with cart badge), flash messages, footer, asset includes. |
| `auth/login.html`, `register.html`, `profile.html` | Authentication pages. |
| `store/index.html`, `products.html`, `product_detail.html` | Storefront pages with add-to-cart forms. |
| `store/cart.html`, `checkout.html`, `orders.html`, `order_detail.html` | Cart and order pages. |
| `admin/*.html` | Admin dashboard, product form, products/orders/users lists, order detail. |
| `errors/403,404,429,500.html` | Friendly error pages. |

### Static assets (`app/static/`)

| Path | Purpose |
|------|---------|
| `css/style.css` | Storefront theme (dark UI, cards, navbar, cart badge). |
| `css/admin.css` | Admin panel styling. |
| `img/products/*.svg` | Bundled demo product images. |
| `img/placeholder.png` | Fallback product image. |

### Scripts (`scripts/`)

| File | Purpose |
|------|---------|
| `seed_data.py` | Seeds the admin user, categories and 16 sample products (with image keys). |
| `generate_images.py` | Generates the local product SVG images. |
| `backup.sh` | Automated MySQL dump + S3 upload backup. |
| `setup_server.sh` | EC2 provisioning (Docker, Nginx, Fail2ban, etc.). |

### Infrastructure & DevOps

| File | Purpose |
|------|---------|
| `docker/Dockerfile` | Production image build (Python + Gunicorn). |
| `docker-compose.yml` | Local stack — app + MySQL + Nginx. |
| `config/nginx.conf` | Reverse proxy, security headers, rate limiting. |
| `jenkins/Jenkinsfile` | CI/CD pipeline (build → test → scan → deploy). |
| `migrations/` | Alembic/Flask-Migrate database migrations. |
| `tests/test_auth.py` | Pytest auth tests. |
| `run.py` | App entry point (`create_app()` → `app.run`). |
| `requirements.txt` | Python dependencies. |
| `.env` / `.env.example` | Environment configuration (secrets, DB, AWS). |

---

## Quick Start (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/ecommerce-devsecops.git
cd ecommerce-devsecops

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Start with Docker Compose
docker-compose up -d

# 4. Run database migrations
docker exec ecommerce_app flask db upgrade

# 5. Seed the admin user + sample catalogue (with product images)
docker exec ecommerce_app python scripts/seed_data.py

# 6. Open browser
open http://localhost
```

**Default admin credentials:** `admin@store.com` / `Admin@123456`

### Running without Docker

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Use development settings (serves cookies over plain HTTP, debug on)
# In .env set:  FLASK_ENV=development
python scripts/seed_data.py     # seed admin + sample products
python run.py                   # http://localhost:5000
```

> **Note:** `FLASK_ENV=production` marks the JWT auth cookies as `Secure`, so they
> are only stored over **HTTPS**. When running locally over plain HTTP, use
> `FLASK_ENV=development` or you will appear unable to log in.

---

## Sample Data & Product Images

The catalogue ships with 16 demo products across 5 categories, each with a
category-themed image bundled in `app/static/img/products/`.

```bash
python scripts/seed_data.py        # inserts admin, categories & products
python scripts/generate_images.py  # (re)generate the product images
```

Images are stored on each product as an `image_key`. Locally bundled images use a
`local/...` key and are served straight from `/static/img/`; in production an AWS
**S3** object key is used instead and served via **CloudFront** (see
`Product.image_url`). Admin-uploaded images are resized and pushed to S3
automatically.

---

## AWS Deployment

1. Launch EC2 (Ubuntu 22.04, t2.medium) in a **private subnet**
2. Run the setup script via Bastion Host:
   ```bash
   ssh -J ubuntu@<bastion-ip> ubuntu@<app-server-ip>
   sudo bash /opt/ecommerce-devsecops/scripts/setup_server.sh
   ```
3. Edit `.env` with RDS endpoint, S3 bucket, CloudFront domain
4. Start: `docker-compose up -d`

---

## Security Features

- ✅ bcrypt/argon2 password hashing
- ✅ JWT in HTTP-only cookies (CSRF protected)
- ✅ SQLAlchemy ORM (no raw SQL)
- ✅ Input sanitization with bleach
- ✅ Rate limiting (Flask-Limiter + Nginx)
- ✅ Fail2ban (SSH + HTTP)
- ✅ RBAC (Customer / Admin)
- ✅ Security headers (CSP, X-Frame-Options, HSTS)
- ✅ AWS WAF rules on ALB
- ✅ TLS 1.2+ via AWS ACM

---

## CI/CD Pipeline (Jenkins)

```
Git Push → Build Docker Image → Run Tests → Security Scan (Trivy) → Deploy to EC2
```

---

## Running Tests

```bash
docker exec ecommerce_app python -m pytest tests/ -v
```

---

## Live Application

> **URL:** https://yourdomain.com  
> **Admin Panel:** https://yourdomain.com/admin
