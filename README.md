# ShopSecure – Cloud-Based E-Commerce DevSecOps Project

![IPSR Capstone](https://img.shields.io/badge/IPSR-Capstone-blue)
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
├── docker/Dockerfile        # Production Docker image
├── docker-compose.yml       # Local dev stack
├── config/nginx.conf        # Nginx reverse proxy + security headers
├── jenkins/Jenkinsfile      # CI/CD pipeline
├── scripts/
│   ├── backup.sh            # Automated DB + S3 backup
│   └── setup_server.sh      # EC2 server setup script
├── tests/                   # Pytest tests
├── requirements.txt
└── .env.example
```

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

# 5. Open browser
open http://localhost
```

**Default admin credentials:** `admin@store.com` / `Admin@123456`

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

---

*IPSR Solutions Ltd – Capstone Project*
