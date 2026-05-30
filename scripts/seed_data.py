#!/usr/bin/env python3
"""
Seed script: creates admin user + sample products/categories.
Run inside the container:
  docker exec ecommerce_app python scripts/seed_data.py
"""

import sys, os
sys.path.insert(0, '/app')

from app import create_app, db, bcrypt
from app.models import User, Category, Product

app = create_app()

CATEGORIES = [
    {"name": "Electronics",    "slug": "electronics"},
    {"name": "Fashion",        "slug": "fashion"},
    {"name": "Home & Kitchen", "slug": "home-kitchen"},
    {"name": "Sports",         "slug": "sports"},
    {"name": "Books",          "slug": "books"},
]

PRODUCTS = [
    # Electronics
    {
        "name":        "Wireless Noise-Cancelling Headphones",
        "description": "Premium over-ear headphones with 40-hour battery life, active noise cancellation, and Hi-Res Audio support. Perfect for music lovers and remote workers.",
        "price":       4999.00,
        "stock":       25,
        "category":    "electronics",
        "image":       "headphones.svg",
    },
    {
        "name":        "Mechanical Gaming Keyboard",
        "description": "RGB backlit mechanical keyboard with Cherry MX Blue switches, anti-ghosting, and USB-C connectivity. Elevate your gaming and typing experience.",
        "price":       2799.00,
        "stock":       40,
        "category":    "electronics",
        "image":       "gaming-keyboard.svg",
    },
    {
        "name":        "4K Ultra HD Smart TV 43\"",
        "description": "Android TV with Dolby Vision, built-in Google Assistant, Netflix & YouTube apps. Crystal-clear display with HDR10+ support.",
        "price":       32999.00,
        "stock":       10,
        "category":    "electronics",
        "image":       "smart-tv.svg",
    },
    {
        "name":        "Wireless Earbuds Pro",
        "description": "True wireless earbuds with active noise cancellation, 30-hour total battery, IPX5 water resistance, and premium sound quality.",
        "price":       1899.00,
        "stock":       60,
        "category":    "electronics",
        "image":       "earbuds.svg",
    },

    # Fashion
    {
        "name":        "Men's Premium Cotton Polo",
        "description": "Classic fit premium cotton polo shirt. Available in multiple colours, perfect for casual and semi-formal occasions. Anti-shrink treated fabric.",
        "price":       799.00,
        "stock":       100,
        "category":    "fashion",
        "image":       "polo-shirt.svg",
    },
    {
        "name":        "Women's Running Sneakers",
        "description": "Lightweight, breathable mesh running shoes with memory foam insole and anti-slip rubber outsole. Ideal for gym, running, and casual wear.",
        "price":       1499.00,
        "stock":       75,
        "category":    "fashion",
        "image":       "sneakers.svg",
    },
    {
        "name":        "Leather Crossbody Bag",
        "description": "Genuine leather crossbody bag with adjustable strap, multiple compartments, and premium YKK zipper. Versatile style for everyday use.",
        "price":       2199.00,
        "stock":       30,
        "category":    "fashion",
        "image":       "crossbody-bag.svg",
    },

    # Home & Kitchen
    {
        "name":        "Stainless Steel Air Fryer 5L",
        "description": "Oil-free cooking with 360° rapid air technology. 8 preset programs, digital touchscreen, and easy-clean non-stick basket. Healthy meals in minutes.",
        "price":       3499.00,
        "stock":       20,
        "category":    "home-kitchen",
        "image":       "air-fryer.svg",
    },
    {
        "name":        "Bamboo Cutting Board Set (3-piece)",
        "description": "Eco-friendly bamboo cutting boards in three sizes. Anti-bacterial surface, juice groove, and non-slip feet. Dishwasher safe.",
        "price":       549.00,
        "stock":       85,
        "category":    "home-kitchen",
        "image":       "cutting-board.svg",
    },
    {
        "name":        "Smart Robotic Vacuum Cleaner",
        "description": "Wi-Fi connected robotic vacuum with laser navigation, auto-empty base, 3000Pa suction, and 120-min runtime. Works with Alexa and Google Home.",
        "price":       14999.00,
        "stock":       8,
        "category":    "home-kitchen",
        "image":       "robot-vacuum.svg",
    },

    # Sports
    {
        "name":        "Adjustable Dumbbell Set 2–24 kg",
        "description": "Space-saving adjustable dumbbells replacing 15 sets. Quick-adjust dial system, durable steel plates, and ergonomic grip handles.",
        "price":       6999.00,
        "stock":       15,
        "category":    "sports",
        "image":       "dumbbell-set.svg",
    },
    {
        "name":        "Yoga Mat Premium Anti-Slip 6mm",
        "description": "Extra-thick 6mm eco-friendly TPE yoga mat with alignment lines, carrying strap, and superior grip on all surfaces. 183 x 61 cm.",
        "price":       899.00,
        "stock":       50,
        "category":    "sports",
        "image":       "yoga-mat.svg",
    },
    {
        "name":        "GPS Running Watch",
        "description": "Multi-sport GPS smartwatch with heart rate monitor, sleep tracking, 5 ATM water resistance, and 14-day battery life. Sync to iOS & Android.",
        "price":       8999.00,
        "stock":       18,
        "category":    "sports",
        "image":       "gps-watch.svg",
    },

    # Books
    {
        "name":        "Clean Code – Robert C. Martin",
        "description": "A handbook of agile software craftsmanship. Essential reading for every developer who wants to write better, more maintainable code.",
        "price":       649.00,
        "stock":       200,
        "category":    "books",
        "image":       "clean-code.svg",
    },
    {
        "name":        "Atomic Habits – James Clear",
        "description": "An easy and proven way to build good habits and break bad ones. The #1 New York Times bestseller with 15 million+ copies sold worldwide.",
        "price":       399.00,
        "stock":       150,
        "category":    "books",
        "image":       "atomic-habits.svg",
    },
    {
        "name":        "The DevOps Handbook",
        "description": "How to create world-class agility, reliability, and security in technology organisations. Co-authored by Gene Kim, Patrick Debois, and Jez Humble.",
        "price":       799.00,
        "stock":       80,
        "category":    "books",
        "image":       "devops-handbook.svg",
    },
]

ADMIN_EMAIL    = "admin@store.com"
ADMIN_NAME     = "ShopSecure Admin"
ADMIN_PASSWORD = "Admin@123456"


def seed():
    with app.app_context():
        # ── Admin user ────────────────────────────────────────────────────────
        admin = User.query.filter_by(email=ADMIN_EMAIL).first()
        if not admin:
            hashed = bcrypt.generate_password_hash(ADMIN_PASSWORD).decode("utf-8")
            admin = User(email=ADMIN_EMAIL, name=ADMIN_NAME,
                         password_hash=hashed, role="admin")
            db.session.add(admin)
            print(f"[+] Created admin user: {ADMIN_EMAIL}")
        else:
            print(f"[=] Admin already exists: {ADMIN_EMAIL}")

        # ── Categories ────────────────────────────────────────────────────────
        cat_map = {}
        for c in CATEGORIES:
            obj = Category.query.filter_by(slug=c["slug"]).first()
            if not obj:
                obj = Category(name=c["name"], slug=c["slug"])
                db.session.add(obj)
                print(f"[+] Created category: {c['name']}")
            else:
                print(f"[=] Category exists: {c['name']}")
            cat_map[c["slug"]] = obj

        db.session.flush()   # assign IDs before products

        # ── Products ──────────────────────────────────────────────────────────
        for p in PRODUCTS:
            image_key = f"local/products/{p['image']}" if p.get("image") else None
            existing = Product.query.filter_by(name=p["name"]).first()
            if not existing:
                category = cat_map.get(p["category"])
                product = Product(
                    name=p["name"],
                    description=p["description"],
                    price=p["price"],
                    stock=p["stock"],
                    category_id=category.id if category else None,
                    image_key=image_key,
                    is_active=True,
                )
                db.session.add(product)
                print(f"[+] Created product: {p['name']}")
            elif image_key and not existing.image_key:
                # backfill image for products seeded before images existed
                existing.image_key = image_key
                print(f"[~] Added image to existing product: {p['name']}")
            else:
                print(f"[=] Product exists: {p['name']}")

        db.session.commit()
        print("\n✅ Seeding complete!")
        print(f"   Admin login → {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"   Products added: {len(PRODUCTS)}")
        print(f"   Categories: {len(CATEGORIES)}")


if __name__ == "__main__":
    seed()
