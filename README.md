# UBC Website - Deployment Guide
## Upadhyay Brothers & Co. | Mandhana, Kanpur

---

## Project Structure
```
ubc-website/
├── app.py                  ← Flask backend (main server)
├── requirements.txt        ← Python packages
├── templates/
│   ├── base.html          ← Shared nav + footer
│   ├── index.html         ← Home page
│   ├── products.html      ← Products page
│   ├── past_work.html     ← Past work & clients
│   ├── admin_login.html   ← Admin login
│   └── admin_dashboard.html ← Admin panel
└── static/
    ├── css/style.css
    ├── js/main.js
    └── images/            ← All product images
```

---

## Default Admin Login Credentials

| Username      | Password       | Role          |
|---------------|----------------|---------------|
| admin         | ubc@admin2024  | Administrator |
| gk.upadhyay   | gku@2024       | G.K. Upadhyay |
| employee1     | emp@2024       | Employee 1    |

> **IMPORTANT:** Change these passwords after first login!

---

## How to Run Locally (Test on your computer)

1. Install Python 3.x from https://python.org
2. Open terminal/command prompt in the project folder
3. Run these commands:

```bash
pip install flask flask-cors gunicorn
python app.py
```

4. Open browser and go to: http://localhost:5000
5. Admin panel: http://localhost:5000/admin

---

## Deploy to Render.com (FREE - Backend)

1. Create a free account at https://render.com
2. Click "New" → "Web Service"
3. Upload/connect your project folder
4. Set these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3
5. Click "Deploy"
6. Copy your Render URL (e.g. https://ubc-website.onrender.com)

> **Note:** Free Render servers "sleep" after 15 min of inactivity. First request after sleep takes ~30 sec. Upgrade to paid plan ($7/mo) to avoid this.

---

## Add New Employees to Admin

Edit `app.py` and add to the `admins` list in `init_db()`:
```python
('new_employee', hash_password('their_password'), 'Employee Name'),
```

---

## Add Certificates
When you receive certificate images/PDFs:
1. Add them to `static/images/` folder
2. Edit `templates/index.html` — find the "Certificates" section
3. Replace the placeholder with actual certificate images

---

## Features Included
- ✅ Hero image slider (4 slides with auto-play)
- ✅ About Us section with company history
- ✅ Products page with 9 products, descriptions & specifications
- ✅ Enquiry Now button/modal on every product
- ✅ Past Work & Clients page with gallery
- ✅ Contact form (saves to database)
- ✅ Admin login with username/password authentication
- ✅ Admin dashboard with all enquiries
- ✅ Mark enquiry as read / delete enquiry
- ✅ Search enquiries in admin panel
- ✅ Professional navy & gold theme
- ✅ Fully responsive (mobile friendly)
- ✅ Animated counters, scroll animations
- ✅ Beautiful footer with map embed
- ✅ Certificate section (placeholder, ready for your certs)
