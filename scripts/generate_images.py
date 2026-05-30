#!/usr/bin/env python3
"""
Generate lightweight local product images (SVG) for the demo catalogue.

These are used when AWS S3 is not configured (e.g. local dev). Each image is a
category-themed gradient tile with an icon and the product name, written to
app/static/img/products/. Re-run any time you change the product list.

    python scripts/generate_images.py
"""

import os

# project_root/app/static/img/products
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "static", "img", "products",
)

# Category → (gradient start, gradient end)
PALETTE = {
    "electronics":  ("#6366f1", "#0ea5e9"),
    "fashion":      ("#ec4899", "#f43f5e"),
    "home-kitchen": ("#f59e0b", "#ef4444"),
    "sports":       ("#10b981", "#14b8a6"),
    "books":        ("#8b5cf6", "#6366f1"),
}

# filename (no ext), display name, icon, category
PRODUCTS = [
    ("headphones",      "Wireless Headphones",      "🎧", "electronics"),
    ("gaming-keyboard", "Mechanical Keyboard",      "⌨️", "electronics"),
    ("smart-tv",        "4K Smart TV",              "📺", "electronics"),
    ("earbuds",         "Wireless Earbuds Pro",     "🎵", "electronics"),
    ("polo-shirt",      "Cotton Polo Shirt",        "👕", "fashion"),
    ("sneakers",        "Running Sneakers",         "👟", "fashion"),
    ("crossbody-bag",   "Leather Crossbody Bag",    "👜", "fashion"),
    ("air-fryer",       "Air Fryer 5L",             "🍟", "home-kitchen"),
    ("cutting-board",   "Bamboo Cutting Boards",    "🔪", "home-kitchen"),
    ("robot-vacuum",    "Robotic Vacuum",           "🤖", "home-kitchen"),
    ("dumbbell-set",    "Adjustable Dumbbells",     "🏋️", "sports"),
    ("yoga-mat",        "Premium Yoga Mat",         "🧘", "sports"),
    ("gps-watch",       "GPS Running Watch",        "⌚", "sports"),
    ("clean-code",      "Clean Code",               "📘", "books"),
    ("atomic-habits",   "Atomic Habits",            "📗", "books"),
    ("devops-handbook", "The DevOps Handbook",      "📙", "books"),
]

SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/>
      <stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.42" r="0.6">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.18"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="800" height="800" fill="url(#g)"/>
  <rect width="800" height="800" fill="url(#glow)"/>
  <circle cx="400" cy="330" r="190" fill="#ffffff" fill-opacity="0.10"/>
  <text x="400" y="380" font-size="200" text-anchor="middle" dominant-baseline="middle">{icon}</text>
  <text x="400" y="620" font-size="46" font-weight="700" text-anchor="middle"
        fill="#ffffff" font-family="Segoe UI, Arial, sans-serif">{name}</text>
  <text x="400" y="685" font-size="26" letter-spacing="3" text-anchor="middle"
        fill="#ffffff" fill-opacity="0.65" font-family="Segoe UI, Arial, sans-serif">SHOPSECURE</text>
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for slug, name, icon, category in PRODUCTS:
        c1, c2 = PALETTE[category]
        svg = SVG.format(c1=c1, c2=c2, icon=icon, name=name)
        path = os.path.join(OUT_DIR, f"{slug}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"[+] {path}")
    print(f"\nDone — {len(PRODUCTS)} images written to {OUT_DIR}")


if __name__ == "__main__":
    main()
