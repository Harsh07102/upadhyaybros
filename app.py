from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import hashlib
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# ── Load .env file if present ─────────────────────────────────────────────────
def load_env(path='.env'):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change_this_before_going_live')

DB_PATH = 'ubc.db'
UPLOAD_FOLDER = 'static/images/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

COMPANY_EMAIL = 'upadhyaybrothers@rediffmail.com'
SMTP_HOST     = 'smtp.gmail.com'
SMTP_PORT     = 587
SMTP_USER     = os.environ.get('SMTP_USER', '')
SMTP_PASS     = os.environ.get('SMTP_PASS', '')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Database ──────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, contact TEXT NOT NULL, email TEXT NOT NULL,
        product TEXT, requirements TEXT, timestamp TEXT NOT NULL, is_read INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        full_name TEXT, email TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, token TEXT UNIQUE NOT NULL,
        expires_at TEXT NOT NULL, used INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT, image_path TEXT,
        issued_by TEXT, issue_date TEXT, cert_number TEXT, created_at TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS hero_slides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        eyebrow TEXT, title TEXT NOT NULL, description TEXT,
        image_path TEXT, sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1, created_at TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS dynamic_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        badge TEXT,
        description TEXT,
        specs TEXT,
        created_at TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        image_path TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(product_id) REFERENCES dynamic_products(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT, client_name TEXT,
        industry TEXT, image_path TEXT, created_at TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, industry TEXT, work_done TEXT,
        location TEXT, created_at TEXT NOT NULL
    )''')

    admins = [
        ('admin',       hash_pw(os.environ.get('ADMIN_PASSWORD', '')), 'Administrator',   COMPANY_EMAIL),
        ('gk.upadhyay', hash_pw(os.environ.get('GK_PASSWORD',    '')), 'G.K. Upadhyay',   COMPANY_EMAIL),
        ('employee1',   hash_pw(os.environ.get('EMP1_PASSWORD',  '')), 'Employee 1',      COMPANY_EMAIL),
    ]
    for a in admins:
        try:
            c.execute('INSERT INTO admins (username,password,full_name,email) VALUES (?,?,?,?)', a)
        except: pass

    conn.commit()
    conn.close()

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def send_reset_email(to_email, name, reset_link):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'UBC Admin — Password Reset Request'
        msg['From'] = SMTP_USER or COMPANY_EMAIL
        msg['To'] = to_email
        html = f"""<html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
          <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
            <div style="background:#0a1628;padding:2rem;text-align:center;">
              <h2 style="color:#c9a84c;margin:0;">UPADHYAY BROTHERS & CO.</h2>
              <p style="color:rgba(255,255,255,0.6);margin:0.3rem 0 0;font-size:0.85rem;">Admin Portal — Password Reset</p>
            </div>
            <div style="padding:2rem;">
              <p>Hello <strong>{name}</strong>,</p>
              <p style="color:#555;">A password reset was requested for your account. Click below to set a new password.</p>
              <div style="text-align:center;margin:2rem 0;">
                <a href="{reset_link}" style="background:#c9a84c;color:#0a1628;padding:14px 32px;border-radius:50px;text-decoration:none;font-weight:700;">Reset My Password</a>
              </div>
              <p style="color:#888;font-size:0.82rem;">⏰ This link expires in <strong>1 hour</strong>. If you did not request this, ignore this email.</p>
              <hr style="border:none;border-top:1px solid #eee;margin:1.5rem 0;">
              <p style="color:#aaa;font-size:0.75rem;text-align:center;">Upadhyay Brothers & Co. · Mandhana, Kanpur Nagar, U.P.</p>
            </div>
          </div>
        </body></html>"""
        msg.attach(MIMEText(html, 'html'))
        if SMTP_USER and SMTP_PASS:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.sendmail(SMTP_USER, to_email, msg.as_string())
        else:
            print(f"\n📧 [DEV MODE] Password reset link for {name}:\n{reset_link}\n")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ── Public Routes ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    conn = get_db()
    slides = conn.execute('SELECT * FROM hero_slides WHERE is_active=1 ORDER BY sort_order ASC').fetchall()
    conn.close()
    return render_template('index.html', slides=slides)

# ── Admin Hero Slider ─────────────────────────────────────────────────────────
@app.route('/admin/slider')
def admin_slider():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    conn = get_db()
    slides = conn.execute('SELECT * FROM hero_slides ORDER BY sort_order ASC').fetchall()
    conn.close()
    return render_template('admin_slider.html', slides=slides)

@app.route('/admin/slider/add', methods=['POST'])
def add_slide():
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    eyebrow     = request.form.get('eyebrow','').strip()
    title       = request.form.get('title','').strip()
    description = request.form.get('description','').strip()
    if not title:
        return jsonify({'success': False, 'message': 'Title is required.'})
    image_path = ''
    f = request.files.get('image')
    if f and f.filename and allowed_file(f.filename):
        filename = str(uuid.uuid4()) + '_' + secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_FOLDER, filename))
        image_path = 'images/uploads/' + filename
    conn = get_db()
    max_order = conn.execute('SELECT COALESCE(MAX(sort_order),0) FROM hero_slides').fetchone()[0]
    cur = conn.execute('INSERT INTO hero_slides (eyebrow,title,description,image_path,sort_order,is_active,created_at) VALUES (?,?,?,?,?,1,?)',
                 (eyebrow, title, description, image_path, max_order+1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': new_id})

@app.route('/admin/slider/edit/<int:sid>', methods=['POST'])
def edit_slide(sid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    eyebrow     = request.form.get('eyebrow','').strip()
    title       = request.form.get('title','').strip()
    description = request.form.get('description','').strip()
    conn = get_db()
    conn.execute('UPDATE hero_slides SET eyebrow=?,title=?,description=? WHERE id=?',
                 (eyebrow, title, description, sid))
    f = request.files.get('image')
    if f and f.filename and allowed_file(f.filename):
        old = conn.execute('SELECT image_path FROM hero_slides WHERE id=?',(sid,)).fetchone()
        if old and old['image_path'] and 'uploads/' in old['image_path']:
            try: os.remove(os.path.join('static', old['image_path']))
            except: pass
        filename = str(uuid.uuid4()) + '_' + secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_FOLDER, filename))
        conn.execute('UPDATE hero_slides SET image_path=? WHERE id=?', ('images/uploads/'+filename, sid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/slider/delete/<int:sid>', methods=['POST'])
def delete_slide(sid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    slide = conn.execute('SELECT image_path FROM hero_slides WHERE id=?',(sid,)).fetchone()
    if slide and slide['image_path'] and 'uploads/' in slide['image_path']:
        try: os.remove(os.path.join('static', slide['image_path']))
        except: pass
    conn.execute('DELETE FROM hero_slides WHERE id=?', (sid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/slider/toggle/<int:sid>', methods=['POST'])
def toggle_slide(sid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    current = conn.execute('SELECT is_active FROM hero_slides WHERE id=?', (sid,)).fetchone()
    if not current:
        conn.close()
        return jsonify({'success': False, 'message': 'Slide not found'})
    new_val = 0 if current['is_active'] else 1
    conn.execute('UPDATE hero_slides SET is_active=? WHERE id=?', (new_val, sid))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'is_active': new_val})

@app.route('/admin/slider/reorder', methods=['POST'])
def reorder_slides():
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    order = request.get_json().get('order', [])
    conn = get_db()
    for i, sid in enumerate(order):
        conn.execute('UPDATE hero_slides SET sort_order=? WHERE id=?', (i, sid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/products')
def products():
    conn = get_db()
    prods = conn.execute('SELECT * FROM dynamic_products ORDER BY created_at ASC').fetchall()
    prod_images = {}
    for p in prods:
        imgs = conn.execute('SELECT * FROM product_images WHERE product_id=? ORDER BY sort_order', (p['id'],)).fetchall()
        prod_images[p['id']] = imgs
    conn.close()
    return render_template('products.html', dynamic_products=prods, prod_images=prod_images)

# ── Admin Products ────────────────────────────────────────────────────────────
@app.route('/admin/products')
def admin_products():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    conn = get_db()
    prods = conn.execute('SELECT * FROM dynamic_products ORDER BY created_at ASC').fetchall()
    prod_images = {}
    for p in prods:
        imgs = conn.execute('SELECT * FROM product_images WHERE product_id=? ORDER BY sort_order', (p['id'],)).fetchall()
        prod_images[p['id']] = imgs
    conn.close()
    return render_template('admin_products.html', prods=prods, prod_images=prod_images)

@app.route('/admin/products/add', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    name        = request.form.get('name','').strip()
    badge       = request.form.get('badge','').strip()
    description = request.form.get('description','').strip()
    specs       = request.form.get('specs','').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Product name is required.'})
    conn = get_db()
    cur = conn.execute('INSERT INTO dynamic_products (name,badge,description,specs,created_at) VALUES (?,?,?,?,?)',
                       (name, badge, description, specs, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    prod_id = cur.lastrowid
    files = request.files.getlist('images')
    for i, f in enumerate(files):
        if f and f.filename and allowed_file(f.filename):
            filename = str(uuid.uuid4()) + '_' + secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            conn.execute('INSERT INTO product_images (product_id,image_path,sort_order) VALUES (?,?,?)',
                         (prod_id, 'images/uploads/' + filename, i))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/products/edit/<int:pid>', methods=['POST'])
def edit_product(pid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    name        = request.form.get('name','').strip()
    badge       = request.form.get('badge','').strip()
    description = request.form.get('description','').strip()
    specs       = request.form.get('specs','').strip()
    conn = get_db()
    conn.execute('UPDATE dynamic_products SET name=?,badge=?,description=?,specs=? WHERE id=?',
                 (name, badge, description, specs, pid))
    # Add new images if uploaded
    files = request.files.getlist('images')
    existing = conn.execute('SELECT COUNT(*) FROM product_images WHERE product_id=?',(pid,)).fetchone()[0]
    for i, f in enumerate(files):
        if f and f.filename and allowed_file(f.filename):
            filename = str(uuid.uuid4()) + '_' + secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            conn.execute('INSERT INTO product_images (product_id,image_path,sort_order) VALUES (?,?,?)',
                         (pid, 'images/uploads/' + filename, existing + i))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/products/delete/<int:pid>', methods=['POST'])
def delete_product(pid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    imgs = conn.execute('SELECT image_path FROM product_images WHERE product_id=?', (pid,)).fetchall()
    for img in imgs:
        if img['image_path'] and 'uploads/' in img['image_path']:
            try: os.remove(os.path.join('static', img['image_path']))
            except: pass
    conn.execute('DELETE FROM product_images WHERE product_id=?', (pid,))
    conn.execute('DELETE FROM dynamic_products WHERE id=?', (pid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/products/delete-image/<int:iid>', methods=['POST'])
def delete_product_image(iid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    img = conn.execute('SELECT image_path FROM product_images WHERE id=?', (iid,)).fetchone()
    if img:
        # Only delete the physical file if it's an uploaded file (not an original bundled image)
        if img['image_path'] and 'uploads/' in img['image_path']:
            try: os.remove(os.path.join('static', img['image_path']))
            except: pass
        # Always remove the DB record
        conn.execute('DELETE FROM product_images WHERE id=?', (iid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/projects/edit/<int:pid>', methods=['POST'])
def edit_project(pid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    title       = request.form.get('title','').strip()
    description = request.form.get('description','').strip()
    client_name = request.form.get('client_name','').strip()
    industry    = request.form.get('industry','').strip()
    conn = get_db()
    conn.execute('UPDATE projects SET title=?,description=?,client_name=?,industry=? WHERE id=?',
                 (title, description, client_name, industry, pid))
    # Replace image if new one uploaded
    f = request.files.get('image')
    if f and f.filename and allowed_file(f.filename):
        old = conn.execute('SELECT image_path FROM projects WHERE id=?', (pid,)).fetchone()
        if old and old['image_path'] and 'uploads' in old['image_path']:
            try: os.remove(os.path.join('static', old['image_path']))
            except: pass
        filename = str(uuid.uuid4()) + '_' + secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_FOLDER, filename))
        conn.execute('UPDATE projects SET image_path=? WHERE id=?', ('images/uploads/' + filename, pid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/clients/edit/<int:cid>', methods=['POST'])
def edit_client(cid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    data = request.get_json()
    conn = get_db()
    conn.execute('UPDATE clients SET name=?,industry=?,work_done=?,location=? WHERE id=?',
                 (data.get('name'), data.get('industry'), data.get('work_done'), data.get('location'), cid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/certificates/edit/<int:cid>', methods=['POST'])
def edit_certificate(cid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    title       = request.form.get('title','').strip()
    description = request.form.get('description','').strip()
    issued_by   = request.form.get('issued_by','').strip()
    issue_date  = request.form.get('issue_date','').strip()
    cert_number = request.form.get('cert_number','').strip()
    conn = get_db()
    conn.execute('UPDATE certificates SET title=?,description=?,issued_by=?,issue_date=?,cert_number=? WHERE id=?',
                 (title, description, issued_by, issue_date, cert_number, cid))
    f = request.files.get('image')
    if f and f.filename and allowed_file(f.filename):
        old = conn.execute('SELECT image_path FROM certificates WHERE id=?', (cid,)).fetchone()
        if old and old['image_path']:
            try: os.remove(os.path.join('static', old['image_path']))
            except: pass
        filename = str(uuid.uuid4()) + '_' + secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_FOLDER, filename))
        conn.execute('UPDATE certificates SET image_path=? WHERE id=?', ('images/uploads/' + filename, cid))
    conn.commit(); conn.close()
    return jsonify({'success': True})
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    imgs = conn.execute('SELECT image_path FROM product_images WHERE product_id=?', (pid,)).fetchall()
    for img in imgs:
        try: os.remove(os.path.join('static', img['image_path']))
        except: pass
    conn.execute('DELETE FROM product_images WHERE product_id=?', (pid,))
    conn.execute('DELETE FROM dynamic_products WHERE id=?', (pid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/applications')
def admin_applications():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    conn = get_db()
    apps = conn.execute('SELECT * FROM job_applications ORDER BY applied_at DESC').fetchall()
    conn.close()
    return render_template('admin_applications.html', apps=apps)

@app.route('/admin/applications/mark-read/<int:aid>', methods=['POST'])
def mark_app_read(aid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    conn.execute('UPDATE job_applications SET is_read=1 WHERE id=?', (aid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/applications/delete/<int:aid>', methods=['POST'])
def delete_application(aid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    app_row = conn.execute('SELECT resume_path FROM job_applications WHERE id=?', (aid,)).fetchone()
    if app_row and app_row['resume_path'] and 'uploads/' in app_row['resume_path']:
        try: os.remove(os.path.join('static', app_row['resume_path']))
        except: pass
    conn.execute('DELETE FROM job_applications WHERE id=?', (aid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/careers')
def careers():
    return render_template('careers.html')

@app.route('/careers/apply', methods=['POST'])
def apply_job():
    full_name  = request.form.get('full_name','').strip()
    phone      = request.form.get('phone','').strip()
    email      = request.form.get('email','').strip()
    position   = request.form.get('position','').strip()
    experience = request.form.get('experience','').strip()
    message    = request.form.get('message','').strip()
    resume_path = ''
    if 'resume' in request.files:
        f = request.files['resume']
        if f and f.filename:
            ext = f.filename.rsplit('.',1)[-1].lower()
            if ext in ['pdf','doc','docx']:
                filename = str(uuid.uuid4()) + '_resume.' + ext
                f.save(os.path.join(UPLOAD_FOLDER, filename))
                resume_path = 'images/uploads/' + filename
    if not full_name or not phone:
        return jsonify({'success': False, 'message': 'Name and phone are required.'})
    conn = get_db()
    conn.execute('INSERT INTO job_applications (full_name,phone,email,position,experience,message,resume_path,applied_at) VALUES (?,?,?,?,?,?,?,?)',
                 (full_name, phone, email, position, experience, message, resume_path,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/past-work')
def past_work():
    conn = get_db()
    projects = conn.execute('SELECT * FROM projects ORDER BY created_at DESC').fetchall()
    clients  = conn.execute('SELECT * FROM clients ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('past_work.html', projects=projects, clients=clients)

# ── Admin Past Work ───────────────────────────────────────────────────────────
@app.route('/admin/past-work')
def admin_past_work():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    conn = get_db()
    projects = conn.execute('SELECT * FROM projects ORDER BY created_at DESC').fetchall()
    clients  = conn.execute('SELECT * FROM clients ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin_past_work.html', projects=projects, clients=clients)

@app.route('/admin/projects/add', methods=['POST'])
def add_project():
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    title       = request.form.get('title','').strip()
    description = request.form.get('description','').strip()
    client_name = request.form.get('client_name','').strip()
    industry    = request.form.get('industry','').strip()
    image_path  = ''
    if 'image' in request.files:
        f = request.files['image']
        if f and f.filename and allowed_file(f.filename):
            filename = str(uuid.uuid4()) + '_' + secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            image_path = 'images/uploads/' + filename
    conn = get_db()
    conn.execute('INSERT INTO projects (title,description,client_name,industry,image_path,created_at) VALUES (?,?,?,?,?,?)',
                 (title, description, client_name, industry, image_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/projects/delete/<int:pid>', methods=['POST'])
def delete_project(pid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    p = conn.execute('SELECT image_path FROM projects WHERE id=?', (pid,)).fetchone()
    if p and p['image_path'] and 'uploads' in p['image_path']:
        try: os.remove(os.path.join('static', p['image_path']))
        except: pass
    conn.execute('DELETE FROM projects WHERE id=?', (pid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/clients/add', methods=['POST'])
def add_client():
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    data = request.get_json()
    conn = get_db()
    conn.execute('INSERT INTO clients (name,industry,work_done,location,created_at) VALUES (?,?,?,?,?)',
                 (data.get('name'), data.get('industry'), data.get('work_done'), data.get('location'),
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/clients/delete/<int:cid>', methods=['POST'])
def delete_client(cid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    conn.execute('DELETE FROM clients WHERE id=?', (cid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/certificates')
def certificates():
    conn = get_db()
    dynamic_certs = conn.execute('SELECT * FROM certificates ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('certificates.html', dynamic_certs=dynamic_certs)

# ── Enquiry ───────────────────────────────────────────────────────────────────
@app.route('/api/enquiry', methods=['POST'])
def submit_enquiry():
    data = request.get_json()
    name = data.get('name','').strip()
    contact = data.get('contact','').strip()
    email = data.get('email','').strip()
    if not name or not contact or not email:
        return jsonify({'success': False, 'message': 'Name, contact and email are required.'}), 400
    conn = get_db()
    conn.execute('INSERT INTO enquiries (name,contact,email,product,requirements,timestamp) VALUES (?,?,?,?,?,?)',
        (name, contact, email, data.get('product',''), data.get('requirements',''), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'message': 'Enquiry submitted successfully!'})

# ── Forgot / Reset Password ───────────────────────────────────────────────────
@app.route('/admin/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        conn = get_db()
        admin = conn.execute('SELECT * FROM admins WHERE username=?', (username,)).fetchone()
        if admin and admin['email']:
            token = str(uuid.uuid4())
            expires = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('INSERT INTO password_resets (username,token,expires_at) VALUES (?,?,?)', (username, token, expires))
            conn.commit()
            reset_link = url_for('reset_password', token=token, _external=True)
            send_reset_email(admin['email'], admin['full_name'], reset_link)
            masked = admin['email'][:3] + '***@' + admin['email'].split('@')[1]
            conn.close()
            return render_template('forgot_password.html', success=True, email=masked)
        conn.close()
        return render_template('forgot_password.html', error='Username not found.')
    return render_template('forgot_password.html')

@app.route('/admin/reset-password/<token>', methods=['GET','POST'])
def reset_password(token):
    conn = get_db()
    reset = conn.execute('SELECT * FROM password_resets WHERE token=? AND used=0 AND expires_at > ?',
                         (token, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))).fetchone()
    if not reset:
        conn.close()
        return render_template('reset_password.html', invalid=True)
    if request.method == 'POST':
        pw = request.form.get('password','')
        cpw = request.form.get('confirm_password','')
        if len(pw) < 6:
            conn.close()
            return render_template('reset_password.html', token=token, error='Password must be at least 6 characters.')
        if pw != cpw:
            conn.close()
            return render_template('reset_password.html', token=token, error='Passwords do not match.')
        conn.execute('UPDATE admins SET password=? WHERE username=?', (hash_pw(pw), reset['username']))
        conn.execute('UPDATE password_resets SET used=1 WHERE token=?', (token,))
        conn.commit(); conn.close()
        return render_template('reset_password.html', success=True)
    conn.close()
    return render_template('reset_password.html', token=token)

# ── Admin Login / Dashboard ───────────────────────────────────────────────────
@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = hash_pw(request.form.get('password',''))
        conn = get_db()
        admin = conn.execute('SELECT * FROM admins WHERE username=? AND password=?', (username, password)).fetchone()
        conn.close()
        if admin:
            session['admin_logged_in'] = True
            session['admin_name'] = admin['full_name']
            session['admin_username'] = admin['username']
            return redirect(url_for('admin_dashboard'))
        error = 'Invalid credentials. Please try again.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    conn = get_db()
    enquiries  = conn.execute('SELECT * FROM enquiries ORDER BY timestamp DESC').fetchall()
    total      = len(enquiries)
    unread     = sum(1 for e in enquiries if not e['is_read'])
    cert_count  = conn.execute('SELECT COUNT(*) FROM certificates').fetchone()[0]
    prod_count  = conn.execute('SELECT COUNT(*) FROM dynamic_products').fetchone()[0]
    slide_count = conn.execute('SELECT COUNT(*) FROM hero_slides WHERE is_active=1').fetchone()[0]
    app_count   = conn.execute('SELECT COUNT(*) FROM job_applications WHERE is_read=0').fetchone()[0]
    conn.close()
    return render_template('admin_dashboard.html', enquiries=enquiries, total=total,
                           unread=unread, cert_count=cert_count,
                           prod_count=prod_count, slide_count=slide_count,
                           app_count=app_count)

@app.route('/admin/mark-read/<int:eid>', methods=['POST'])
def mark_read(eid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    conn.execute('UPDATE enquiries SET is_read=1 WHERE id=?', (eid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/delete/<int:eid>', methods=['POST'])
def delete_enquiry(eid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    conn.execute('DELETE FROM enquiries WHERE id=?', (eid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# ── Admin Certificates ────────────────────────────────────────────────────────
@app.route('/admin/certificates')
def admin_certificates():
    if not session.get('admin_logged_in'): return redirect(url_for('admin_login'))
    conn = get_db()
    certs = conn.execute('SELECT * FROM certificates ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin_certificates.html', certs=certs)

@app.route('/admin/certificates/add', methods=['POST'])
def add_certificate():
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    title = request.form.get('title','').strip()
    description = request.form.get('description','').strip()
    issued_by = request.form.get('issued_by','').strip()
    issue_date = request.form.get('issue_date','').strip()
    cert_number = request.form.get('cert_number','').strip()
    image_path = ''
    if 'image' in request.files:
        f = request.files['image']
        if f and f.filename and allowed_file(f.filename):
            filename = str(uuid.uuid4()) + '_' + secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_FOLDER, filename))
            image_path = 'images/uploads/' + filename
    conn = get_db()
    conn.execute('INSERT INTO certificates (title,description,image_path,issued_by,issue_date,cert_number,created_at) VALUES (?,?,?,?,?,?,?)',
                 (title, description, image_path, issued_by, issue_date, cert_number, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'message': 'Certificate added!'})

@app.route('/admin/certificates/delete/<int:cid>', methods=['POST'])
def delete_certificate(cid):
    if not session.get('admin_logged_in'): return jsonify({'success': False}), 401
    conn = get_db()
    cert = conn.execute('SELECT image_path FROM certificates WHERE id=?', (cid,)).fetchone()
    if cert and cert['image_path']:
        try: os.remove(os.path.join('static', cert['image_path']))
        except: pass
    conn.execute('DELETE FROM certificates WHERE id=?', (cid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=False, port=5001, host='0.0.0.0')
