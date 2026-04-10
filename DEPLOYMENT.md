# UBC Website — Deployment & Security Guide

## Before Going Live — Checklist

### 1. Set a Strong Secret Key
Open `.env` and replace the SECRET_KEY with a random string.
Generate one by running this command on your server:
```
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Paste the output into `.env`:
```
SECRET_KEY=a3f8c2e1d9b4...your_generated_key_here
```

### 2. Change All Admin Passwords
In `.env`, set strong passwords before first run:
```
ADMIN_PASSWORD=YourStrongPassword123!
GK_PASSWORD=AnotherStrongPassword!
EMP1_PASSWORD=ThirdStrongPassword!
```
These are only used on the **very first run** to seed the database.
After that, change passwords through the admin panel directly.

### 3. Keep .env Private
- NEVER share the `.env` file
- NEVER commit it to Git (already in `.gitignore`)
- Keep it only on the server

---

## Recommended Hosting Setup (Free / Low Cost)

### Option A — VPS (Recommended)
Use any VPS: DigitalOcean, Vultr, Hostinger VPS (~₹300–500/month)

**Install dependencies:**
```bash
pip install flask werkzeug gunicorn python-dotenv
```

**Run with Gunicorn (production server):**
```bash
gunicorn -w 2 -b 127.0.0.1:5000 app:app
```

**Use Nginx as reverse proxy + HTTPS via Certbot (free SSL):**
```nginx
server {
    server_name yourdomain.com www.yourdomain.com;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
```bash
sudo certbot --nginx -d yourdomain.com
```

### Option B — PythonAnywhere (Easiest, Free tier available)
1. Upload your files to PythonAnywhere
2. Set environment variables in their dashboard
3. Configure WSGI to point to `app:app`

---

## DO NOT Use in Production
- `python3 app.py` → This uses Flask's dev server (not safe, single user only)
- `debug=True` → Already fixed to read from `.env` (defaults to false)

---

## Files to Upload to Server
```
ubc-website/
├── app.py
├── .env          ← Create this on server, fill in your values
├── requirements.txt
├── ubc.db
├── static/
└── templates/
```

## Install Requirements
```bash
pip install -r requirements.txt
```

## First Run (creates database + admin accounts)
```bash
python3 -c "import app; app.init_db()"
```

---

## Security Summary

| What | Status |
|------|--------|
| Secret key in code | ✅ Fixed — now in .env |
| Passwords in code | ✅ Fixed — now in .env |
| Debug mode | ✅ Fixed — defaults to OFF |
| Admin auth on all routes | ✅ All admin routes protected |
| File upload validation | ✅ Only images/PDFs allowed |
| SQL injection | ✅ Parameterised queries used |
| HTTPS | ⚠️ Set up via Certbot on your server |
