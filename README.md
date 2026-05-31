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
          PostgreSQL (RDS)   S3 + CloudFront         CloudWatch
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
│   ├── __init__.py          # App factory (auto-initializes DB tables)
│   ├── config.py            # Configuration classes
│   ├── models.py            # SQLAlchemy models
│   ├── utils.py             # S3 upload, sanitization, decorators
│   ├── auth/routes.py       # Register, login, logout
│   ├── store/routes.py      # Products, cart, checkout, orders
│   ├── admin/routes.py      # Admin dashboard + CRUD
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, images
│       └── img/products/    # Bundled demo product images (SVG)
├── docker/Dockerfile        # Production Docker image (if not using Vercel)
├── docker-compose.yml       # Local dev stack (PostgreSQL + Nginx)
├── config/nginx.conf        # Nginx reverse proxy + security headers
├── vercel.json              # Vercel Serverless deployment config
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

## Repository Files – Detailed Reference

### Application core (`app/`)

| File | Responsibility |
|------|----------------|
| `app/__init__.py` | **App factory** (`create_app`). Initializes SQLAlchemy, Migrate, JWT, Bcrypt, Flask-Limiter and CSRF; auto-creates DB tables on first run; defines health checks and file/stdout logging. |
| `app/config.py` | Configuration classes – `BaseConfig`, `Development`, `Production`, `Testing`. Holds DB URI (Postgres), JWT/cookie settings, S3/CloudFront. |
| `app/models.py` | SQLAlchemy models: **User, Category, Product, Cart, Order, OrderItem**, including the `Product.image_url` property (local / S3 / CloudFront). |
| `app/utils.py` | Shared helpers – input `sanitize()` (bleach), decorators, `current_user()`, and S3 image upload/delete. |

### Blueprints (routes)

| File | Responsibility |
|------|----------------|
| `app/auth/routes.py` | Register, login, logout, profile. Validates input, hashes passwords with bcrypt, issues JWT cookies. |
| `app/store/routes.py` | Storefront – home, product list/search, cart, checkout, order history. |
| `app/admin/routes.py` | Admin panel – dashboard stats, product CRUD, order updates, user management. Protected by `@admin_required`. |

### Infrastructure & DevOps

| File | Purpose |
|------|---------|
| `vercel.json` | Production Serverless deployment configuration for Vercel. |
| `docker-compose.yml` | Local stack – app + PostgreSQL + Nginx. |
| `config/nginx.conf` | Reverse proxy, security headers, rate limiting (if using EC2). |
| `run.py` | Local App entry point (`create_app()` + `app.run`). |
| `.env.example` | Environment configuration (secrets, DB, AWS). |

---

## Quick Start (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/ecommerce-devsecops.git
cd ecommerce-devsecops

# 2. Configure environment
cp .env.example .env
# Edit .env with your values (ensure DATABASE_URL points to a PostgreSQL database)

# 3. Start with Docker Compose
docker-compose up -d

# 4. Open browser
open http://localhost
```

**Default admin credentials:** `admin@store.com` / `Admin@123456`

### Running without Docker

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Use development settings (serves cookies over plain HTTP, debug on)
# In .env set:  FLASK_ENV=development
python run.py                   # http://localhost:5000
```

> **Note:** The app automatically creates all database tables and seeds demo products the first time it connects to the database, so there is no need to run manual migrations for fresh installs!

---

## Vercel Deployment (Recommended)

This application is fully optimized for **Vercel Serverless Functions**.

1. Import this repository into Vercel.
2. In the Vercel Dashboard, go to **Settings > Environment Variables** and add:
   - `DATABASE_URL` (e.g., your Neon PostgreSQL connection string)
   - `SECRET_KEY`, `JWT_SECRET_KEY`
   - (Optional) `S3_BUCKET`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` for image uploads.
   - `FLASK_ENV=production`
3. Click **Deploy**. Vercel will automatically run `pip install`, connect to your PostgreSQL database, and serve the application!

---

## AWS Deployment (EC2 Alternative)

1. Launch EC2 (Ubuntu 22.04, t2.medium) in a **private subnet**
2. Run the setup script via Bastion Host:
   ```bash
   ssh -J ubuntu@<bastion-ip> ubuntu@<app-server-ip>
   sudo bash /opt/ecommerce-devsecops/scripts/setup_server.sh
   ```
3. Edit `.env` with RDS PostgreSQL endpoint, S3 bucket, CloudFront domain
4. Start: `docker-compose up -d`

---

## Security Features

- 🛡 bcrypt password hashing
- 🛡 JWT in HTTP-only cookies (CSRF protected)
- 🛡 SQLAlchemy ORM (SQL Injection prevention)
- 🛡 Input sanitization with bleach (XSS prevention)
- 🛡 Serverless read-only filesystem (Vercel)
- 🛡 Secrets completely decoupled from source code
- 🛡 RBAC (Customer / Admin)
- 🛡 Security headers (CSP, X-Frame-Options, HSTS)
- 🛡 AWS WAF rules on ALB (if EC2 deployed)
- 🛡 TLS 1.2+ via AWS ACM (or Vercel Edge Network)

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
