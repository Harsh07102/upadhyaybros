"""
migrate.py — Run this once if you get "no such table" errors.
It safely adds any missing tables WITHOUT deleting existing data.

Usage:  python3 migrate.py
"""
import sqlite3
from datetime import datetime

DB_PATH = 'ubc.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("🔧 Running UBC database migration...")

# ── Enquiries ──────────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS enquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, contact TEXT NOT NULL, email TEXT NOT NULL,
    product TEXT, requirements TEXT, timestamp TEXT NOT NULL, is_read INTEGER DEFAULT 0
)''')
print("  ✅ enquiries table ready")

# ── Admins ─────────────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
    full_name TEXT, email TEXT
)''')
# Add email column if it doesn't exist yet
try:
    c.execute("ALTER TABLE admins ADD COLUMN email TEXT")
    print("  ✅ Added email column to admins")
except: pass
print("  ✅ admins table ready")

# ── Password Resets ────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL, token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL, used INTEGER DEFAULT 0
)''')
print("  ✅ password_resets table ready")

# ── Certificates ───────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL, description TEXT, image_path TEXT,
    issued_by TEXT, issue_date TEXT, cert_number TEXT, created_at TEXT NOT NULL
)''')
print("  ✅ certificates table ready")

# ── Flashcards ─────────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL, category TEXT,
    front_content TEXT NOT NULL, back_content TEXT NOT NULL,
    color TEXT DEFAULT 'navy', created_by TEXT, created_at TEXT NOT NULL
)''')
print("  ✅ flashcards table ready")

c.execute('''CREATE TABLE IF NOT EXISTS hero_slides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eyebrow TEXT, title TEXT NOT NULL, description TEXT,
    image_path TEXT, sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1, created_at TEXT NOT NULL
)''')
print("  ✅ hero_slides table ready")

c.execute('''CREATE TABLE IF NOT EXISTS dynamic_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, badge TEXT, description TEXT,
    specs TEXT, created_at TEXT NOT NULL
)''')
print("  ✅ dynamic_products table ready")

c.execute('''CREATE TABLE IF NOT EXISTS product_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL, image_path TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY(product_id) REFERENCES dynamic_products(id)
)''')
print("  ✅ product_images table ready")

# ── Projects (Past Work) ───────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL, description TEXT, client_name TEXT,
    industry TEXT, image_path TEXT, created_at TEXT NOT NULL
)''')
print("  ✅ projects table ready")

# ── Clients ────────────────────────────────────────────────────────────────────
c.execute('''CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, industry TEXT, work_done TEXT,
    location TEXT, created_at TEXT NOT NULL
)''')
print("  ✅ clients table ready")

conn.commit()
conn.close()
print("\n🎉 Migration complete! All tables are up to date.")
print("   You can now start the app with:  python3 app.py")
