"""
TRAVELOOP - Main Flask Application
AI-powered Travel Planning Platform
"""

import os
import sqlite3
import uuid
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
import time

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ──────────────────────────────────────────────
# App Configuration
# ──────────────────────────────────────────────
FRONTEND_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../frontend')
app = Flask(__name__, static_folder=FRONTEND_FOLDER, static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'traveloop-secret-2024-hackathon')
CORS(app, supports_credentials=True)

# File upload config
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Email config (update with your Gmail credentials)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = os.environ.get('EMAIL_USER', 'urvilgajjar@gmail.com')
EMAIL_PASS = os.environ.get('EMAIL_PASS', 'bzgimuxmtsqzcskk')

DB_PATH = 'traveloop.db'

# ──────────────────────────────────────────────
# Database Helpers
# ──────────────────────────────────────────────
def get_db():
    """Get SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize DB from schema.sql."""
    conn = get_db()
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("✅ Database initialized.")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ──────────────────────────────────────────────
# Auth Helpers
# ──────────────────────────────────────────────
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(to_email, otp, name="Traveler"):
    """Send OTP via Gmail SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🌍 Traveloop - Your OTP: {otp}"
        msg['From'] = EMAIL_USER
        msg['To'] = to_email

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#0f0f1a;color:#fff;border-radius:16px;overflow:hidden;">
          <div style="background:linear-gradient(135deg,#6c3de8,#3b82f6);padding:32px;text-align:center;">
            <h1 style="margin:0;font-size:28px;letter-spacing:2px;">✈️ TRAVELOOP</h1>
            <p style="margin:8px 0 0;opacity:0.8;">Your adventure awaits!</p>
          </div>
          <div style="padding:32px;">
            <h2 style="color:#a78bfa;">Hey {name}! 👋</h2>
            <p style="color:#cbd5e1;">Here's your One-Time Password to verify your account:</p>
            <div style="background:#1e1b4b;border:2px solid #6c3de8;border-radius:12px;padding:24px;text-align:center;margin:24px 0;">
              <span style="font-size:40px;font-weight:bold;letter-spacing:12px;color:#a78bfa;">{otp}</span>
            </div>
            <p style="color:#94a3b8;font-size:14px;">⏱ This OTP expires in 10 minutes.</p>
            <p style="color:#94a3b8;font-size:14px;">If you didn't request this, ignore this email.</p>
          </div>
          <div style="padding:16px 32px;border-top:1px solid #1e293b;text-align:center;color:#475569;font-size:12px;">
            © 2024 Traveloop — Plan smarter, travel better.
          </div>
        </div>
        """
        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def login_required(f):
    """Decorator to protect API routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized. Please log in.'}), 401
        return f(*args, **kwargs)
    return decorated


def current_user_id():
    return session.get('user_id')


# ──────────────────────────────────────────────
# Page Routes (HTML)
# ──────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(FRONTEND_FOLDER, 'dashboard.html')

@app.route('/login')
def login_page():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/verify')
def verify_page():
    return send_from_directory(FRONTEND_FOLDER, 'verify.html')

@app.route('/dashboard')
def dashboard_page():
    return send_from_directory(FRONTEND_FOLDER, 'dashboard.html')

@app.route('/trips')
def trips_page():
    return send_from_directory(FRONTEND_FOLDER, 'trips.html')

@app.route('/trips/new')
def new_trip_page():
    return send_from_directory(FRONTEND_FOLDER, 'create_trip.html')

@app.route('/trips/<int:trip_id>')
def trip_detail_page(trip_id):
    return send_from_directory(FRONTEND_FOLDER, 'trip_detail.html')

@app.route('/share/<share_token>')
def public_share_page(share_token):
    return send_from_directory(FRONTEND_FOLDER, 'share.html')

@app.route('/profile')
def profile_page():
    return send_from_directory(FRONTEND_FOLDER, 'profile.html')

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/ai-planner')
def ai_planner_page():
    return send_from_directory(FRONTEND_FOLDER, 'ai_planner.html')

@app.route('/<path:filename>')
def custom_static(filename):
    if os.path.exists(os.path.join(FRONTEND_FOLDER, filename)):
        return send_from_directory(FRONTEND_FOLDER, filename)
    return send_from_directory(FRONTEND_FOLDER, '404.html'), 404


# ══════════════════════════════════════════════
# AUTH APIs
# ══════════════════════════════════════════════

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not all([name, email, password]):
        return jsonify({'error': 'All fields are required.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    conn = get_db()
    try:
        existing = conn.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
        if existing:
            return jsonify({'error': 'Email already registered.'}), 409

        otp = generate_otp()
        otp_expiry = (datetime.now() + timedelta(minutes=10)).isoformat()
        hashed = generate_password_hash(password)

        conn.execute(
            'INSERT INTO users (name, email, password, otp, otp_expiry) VALUES (?,?,?,?,?)',
            (name, email, hashed, otp, otp_expiry)
        )
        conn.commit()

        # Store email in session for verification
        session['pending_email'] = email

        # Try sending email, fallback for dev
        sent = send_otp_email(email, otp, name)
        msg = 'OTP sent to your email.' if sent else f'Dev mode: OTP is {otp}'

        return jsonify({'success': True, 'message': msg}), 201
    finally:
        conn.close()


@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email') or session.get('pending_email', '')
    if email:
        email = email.strip().lower()
    otp = data.get('otp', '').strip()

    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required.'}), 400

    conn = get_db()
    try:
        user = conn.execute(
            'SELECT * FROM users WHERE email=?', (email,)
        ).fetchone()

        if not user:
            return jsonify({'error': 'User not found.'}), 404
        if user['is_verified']:
            return jsonify({'error': 'Already verified. Please login.'}), 400
        if user['otp'] != otp:
            return jsonify({'error': 'Invalid OTP.'}), 400
        if datetime.fromisoformat(user['otp_expiry']) < datetime.now():
            return jsonify({'error': 'OTP expired. Please signup again.'}), 400

        conn.execute(
            'UPDATE users SET is_verified=1, otp=NULL, otp_expiry=NULL WHERE email=?',
            (email,)
        )
        conn.commit()

        # Auto login after verification
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session.pop('pending_email', None)

        return jsonify({'success': True, 'message': 'Account verified! Welcome to Traveloop.'})
    finally:
        conn.close()


@app.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    data = request.json
    email = data.get('email') or session.get('pending_email', '')
    if email:
        email = email.strip().lower()

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if not user:
            return jsonify({'error': 'User not found.'}), 404

        otp = generate_otp()
        otp_expiry = (datetime.now() + timedelta(minutes=10)).isoformat()
        conn.execute('UPDATE users SET otp=?, otp_expiry=? WHERE email=?', (otp, otp_expiry, email))
        conn.commit()

        sent = send_otp_email(email, otp, user['name'])
        msg = 'New OTP sent!' if sent else f'Dev OTP: {otp}'
        return jsonify({'success': True, 'message': msg})
    finally:
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    conn = get_db()
    try:
        user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if not user:
            return jsonify({'error': 'Invalid email or password.'}), 401
        if not user['is_verified']:
            session['pending_email'] = email
            return jsonify({'error': 'Please verify your email first.', 'redirect': '/verify'}), 403
        if not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid email or password.'}), 401

        session['user_id'] = user['id']
        session['user_name'] = user['name']

        return jsonify({
            'success': True,
            'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'avatar': user['avatar']}
        })
    finally:
        conn.close()


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/me', methods=['GET'])
@login_required
def get_me():
    conn = get_db()
    try:
        user = conn.execute(
            'SELECT id, name, email, avatar, created_at FROM users WHERE id=?',
            (current_user_id(),)
        ).fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(dict(user))
    finally:
        conn.close()


# ══════════════════════════════════════════════
# PROFILE APIs
# ══════════════════════════════════════════════

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.json
    name = data.get('name', '').strip()
    conn = get_db()
    try:
        conn.execute('UPDATE users SET name=?, updated_at=? WHERE id=?',
                     (name, datetime.now().isoformat(), current_user_id()))
        conn.commit()
        session['user_name'] = name
        return jsonify({'success': True, 'message': 'Profile updated.'})
    finally:
        conn.close()


@app.route('/api/profile/avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400
    file = request.files['avatar']
    if file and allowed_file(file.filename):
        filename = f"avatar_{current_user_id()}_{uuid.uuid4().hex[:8]}.{file.filename.rsplit('.',1)[1]}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        conn = get_db()
        conn.execute('UPDATE users SET avatar=? WHERE id=?', (filename, current_user_id()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'avatar': filename})
    return jsonify({'error': 'Invalid file type.'}), 400


@app.route('/api/profile', methods=['DELETE'])
@login_required
def delete_account():
    conn = get_db()
    try:
        conn.execute('DELETE FROM users WHERE id=?', (current_user_id(),))
        conn.commit()
        session.clear()
        return jsonify({'success': True, 'message': 'Account deleted.'})
    finally:
        conn.close()


# ══════════════════════════════════════════════
# TRIPS APIs
# ══════════════════════════════════════════════

@app.route('/api/trips', methods=['GET'])
@login_required
def get_trips():
    conn = get_db()
    try:
        trips = conn.execute(
            '''SELECT t.*, 
               (SELECT COUNT(*) FROM trip_stops WHERE trip_id=t.id) as stop_count,
               (SELECT COALESCE(SUM(amount),0) FROM budgets WHERE trip_id=t.id) as spent
               FROM trips t WHERE t.user_id=? ORDER BY t.created_at DESC''',
            (current_user_id(),)
        ).fetchall()
        return jsonify([dict(t) for t in trips])
    finally:
        conn.close()


@app.route('/api/trips', methods=['POST'])
@login_required
def create_trip():
    data = request.json
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Trip title is required.'}), 400

    share_token = uuid.uuid4().hex
    conn = get_db()
    try:
        cur = conn.execute(
            '''INSERT INTO trips (user_id, title, description, start_date, end_date, total_budget, status, share_token)
               VALUES (?,?,?,?,?,?,?,?)''',
            (current_user_id(), title, data.get('description'), data.get('start_date'),
             data.get('end_date'), data.get('total_budget', 0), 'planning', share_token)
        )
        conn.commit()
        trip_id = cur.lastrowid

        # Automatically add the first stop if city is provided
        city_input = data.get('city', '').strip()
        if city_input:
            # Try to separate city and country if user provided "City, Country"
            city_parts = [p.strip() for p in city_input.split(',')]
            city = city_parts[0]
            country = city_parts[1] if len(city_parts) > 1 else city # Fallback to city name for country
            
            conn.execute(
                'INSERT INTO trip_stops (trip_id, city, country, arrival_date, departure_date, order_index) VALUES (?,?,?,?,?,?)',
                (trip_id, city, country, data.get('start_date'), data.get('end_date'), 0)
            )
            conn.commit()

        trip = conn.execute('SELECT * FROM trips WHERE id=?', (trip_id,)).fetchone()
        return jsonify(dict(trip)), 201
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>', methods=['GET'])
@login_required
def get_trip(trip_id):
    conn = get_db()
    try:
        trip = conn.execute(
            'SELECT * FROM trips WHERE id=? AND user_id=?',
            (trip_id, current_user_id())
        ).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found.'}), 404

        stops = conn.execute(
            'SELECT * FROM trip_stops WHERE trip_id=? ORDER BY order_index', (trip_id,)
        ).fetchall()

        activities = conn.execute(
            'SELECT * FROM trip_activities WHERE trip_id=? ORDER BY date, time', (trip_id,)
        ).fetchall()

        budgets = conn.execute(
            'SELECT * FROM budgets WHERE trip_id=?', (trip_id,)
        ).fetchall()

        notes = conn.execute(
            'SELECT * FROM notes WHERE trip_id=? ORDER BY trip_day, created_at', (trip_id,)
        ).fetchall()

        packing = conn.execute(
            'SELECT * FROM packing_items WHERE trip_id=? ORDER BY category, item_name', (trip_id,)
        ).fetchall()

        result = dict(trip)
        result['stops'] = [dict(s) for s in stops]
        result['activities'] = [dict(a) for a in activities]
        result['budgets'] = [dict(b) for b in budgets]
        result['notes'] = [dict(n) for n in notes]
        result['packing'] = [dict(p) for p in packing]
        return jsonify(result)
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>', methods=['PUT'])
@login_required
def update_trip(trip_id):
    data = request.json
    conn = get_db()
    try:
        trip = conn.execute('SELECT id FROM trips WHERE id=? AND user_id=?', (trip_id, current_user_id())).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found.'}), 404
        conn.execute(
            '''UPDATE trips SET title=?, description=?, start_date=?, end_date=?,
               total_budget=?, status=?, updated_at=? WHERE id=?''',
            (data.get('title'), data.get('description'), data.get('start_date'),
             data.get('end_date'), data.get('total_budget', 0), data.get('status', 'planning'),
             datetime.now().isoformat(), trip_id)
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Trip updated.'})
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>', methods=['DELETE'])
@login_required
def delete_trip(trip_id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM trips WHERE id=? AND user_id=?', (trip_id, current_user_id()))
        conn.commit()
        return jsonify({'success': True, 'message': 'Trip deleted.'})
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>/cover', methods=['POST'])
@login_required
def upload_cover(trip_id):
    if 'cover' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400
    file = request.files['cover']
    if file and allowed_file(file.filename):
        filename = f"cover_{trip_id}_{uuid.uuid4().hex[:8]}.{file.filename.rsplit('.',1)[1]}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db()
        conn.execute('UPDATE trips SET cover_image=? WHERE id=? AND user_id=?',
                     (filename, trip_id, current_user_id()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'cover_image': filename})
    return jsonify({'error': 'Invalid file.'}), 400


@app.route('/api/trips/<int:trip_id>/share', methods=['POST'])
@login_required
def toggle_share(trip_id):
    conn = get_db()
    try:
        trip = conn.execute('SELECT * FROM trips WHERE id=? AND user_id=?', (trip_id, current_user_id())).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found.'}), 404
        new_public = 0 if trip['is_public'] else 1
        conn.execute('UPDATE trips SET is_public=? WHERE id=?', (new_public, trip_id))
        conn.commit()
        return jsonify({'success': True, 'is_public': bool(new_public), 'share_token': trip['share_token']})
    finally:
        conn.close()


# Public share endpoint
@app.route('/api/share/<share_token>', methods=['GET'])
def get_shared_trip(share_token):
    conn = get_db()
    try:
        trip = conn.execute(
            'SELECT t.*, u.name as author FROM trips t JOIN users u ON t.user_id=u.id WHERE t.share_token=? AND t.is_public=1',
            (share_token,)
        ).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found or not public.'}), 404

        stops = conn.execute('SELECT * FROM trip_stops WHERE trip_id=? ORDER BY order_index', (trip['id'],)).fetchall()
        activities = conn.execute('SELECT * FROM trip_activities WHERE trip_id=? ORDER BY date', (trip['id'],)).fetchall()

        result = dict(trip)
        result['stops'] = [dict(s) for s in stops]
        result['activities'] = [dict(a) for a in activities]
        return jsonify(result)
    finally:
        conn.close()


# ══════════════════════════════════════════════
# TRIP STOPS APIs
# ══════════════════════════════════════════════

@app.route('/api/trips/<int:trip_id>/stops', methods=['POST'])
@login_required
def add_stop(trip_id):
    data = request.json
    conn = get_db()
    try:
        # verify ownership
        trip = conn.execute('SELECT id FROM trips WHERE id=? AND user_id=?', (trip_id, current_user_id())).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found.'}), 404

        count = conn.execute('SELECT COUNT(*) as c FROM trip_stops WHERE trip_id=?', (trip_id,)).fetchone()['c']
        cur = conn.execute(
            'INSERT INTO trip_stops (trip_id, city, country, arrival_date, departure_date, notes, order_index) VALUES (?,?,?,?,?,?,?)',
            (trip_id, data.get('city'), data.get('country', ''), data.get('arrival_date'),
             data.get('departure_date'), data.get('notes'), count)
        )
        conn.commit()
        stop = conn.execute('SELECT * FROM trip_stops WHERE id=?', (cur.lastrowid,)).fetchone()
        return jsonify(dict(stop)), 201
    finally:
        conn.close()


@app.route('/api/stops/<int:stop_id>', methods=['PUT'])
@login_required
def update_stop(stop_id):
    data = request.json
    conn = get_db()
    try:
        conn.execute(
            'UPDATE trip_stops SET city=?, country=?, arrival_date=?, departure_date=?, notes=? WHERE id=?',
            (data.get('city'), data.get('country'), data.get('arrival_date'), data.get('departure_date'), data.get('notes'), stop_id)
        )
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/stops/<int:stop_id>', methods=['DELETE'])
@login_required
def delete_stop(stop_id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM trip_stops WHERE id=?', (stop_id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


# ══════════════════════════════════════════════
# ACTIVITIES APIs
# ══════════════════════════════════════════════

@app.route('/api/activities/search', methods=['GET'])
@login_required
def search_activities():
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    conn = get_db()
    try:
        query = 'SELECT * FROM activities WHERE 1=1'
        params = []
        if q:
            query += ' AND (name LIKE ? OR city LIKE ? OR country LIKE ?)'
            params += [f'%{q}%', f'%{q}%', f'%{q}%']
        if category:
            query += ' AND category=?'
            params.append(category)
        query += ' LIMIT 20'
        rows = conn.execute(query, params).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>/activities', methods=['POST'])
@login_required
def add_activity(trip_id):
    data = request.json
    conn = get_db()
    try:
        trip = conn.execute('SELECT id FROM trips WHERE id=? AND user_id=?', (trip_id, current_user_id())).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found.'}), 404
        cur = conn.execute(
            '''INSERT INTO trip_activities (trip_id, stop_id, name, category, date, time, duration_hours, cost, notes)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (trip_id, data.get('stop_id'), data.get('name'), data.get('category', 'sightseeing'),
             data.get('date'), data.get('time'), data.get('duration_hours', 1),
             data.get('cost', 0), data.get('notes'))
        )
        conn.commit()
        act = conn.execute('SELECT * FROM trip_activities WHERE id=?', (cur.lastrowid,)).fetchone()
        return jsonify(dict(act)), 201
    finally:
        conn.close()


@app.route('/api/activities/<int:act_id>', methods=['PUT'])
@login_required
def update_activity(act_id):
    data = request.json
    conn = get_db()
    try:
        conn.execute(
            'UPDATE trip_activities SET name=?, category=?, date=?, time=?, duration_hours=?, cost=?, notes=?, is_completed=? WHERE id=?',
            (data.get('name'), data.get('category'), data.get('date'), data.get('time'),
             data.get('duration_hours', 1), data.get('cost', 0), data.get('notes'), data.get('is_completed', 0), act_id)
        )
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/activities/<int:act_id>', methods=['DELETE'])
@login_required
def delete_activity(act_id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM trip_activities WHERE id=?', (act_id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


# ══════════════════════════════════════════════
# BUDGET APIs
# ══════════════════════════════════════════════

@app.route('/api/trips/<int:trip_id>/budget', methods=['GET'])
@login_required
def get_budget(trip_id):
    conn = get_db()
    try:
        trip = conn.execute('SELECT * FROM trips WHERE id=? AND user_id=?', (trip_id, current_user_id())).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found.'}), 404

        items = conn.execute('SELECT * FROM budgets WHERE trip_id=? ORDER BY created_at DESC', (trip_id,)).fetchall()
        total_spent = conn.execute('SELECT COALESCE(SUM(amount),0) as t FROM budgets WHERE trip_id=?', (trip_id,)).fetchone()['t']

        by_category = conn.execute(
            'SELECT category, COALESCE(SUM(amount),0) as total FROM budgets WHERE trip_id=? GROUP BY category',
            (trip_id,)
        ).fetchall()

        # Activity costs
        act_total = conn.execute(
            'SELECT COALESCE(SUM(cost),0) as t FROM trip_activities WHERE trip_id=?', (trip_id,)
        ).fetchone()['t']

        return jsonify({
            'budget': trip['total_budget'],
            'spent': total_spent,
            'remaining': trip['total_budget'] - total_spent,
            'activity_estimated': act_total,
            'items': [dict(i) for i in items],
            'by_category': [dict(c) for c in by_category]
        })
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>/budget', methods=['POST'])
@login_required
def add_budget_item(trip_id):
    data = request.json
    conn = get_db()
    try:
        cur = conn.execute(
            'INSERT INTO budgets (trip_id, category, amount, currency, notes, date) VALUES (?,?,?,?,?,?)',
            (trip_id, data.get('category', 'misc'), data.get('amount', 0),
             data.get('currency', 'INR'), data.get('notes'), data.get('date'))
        )
        conn.commit()
        item = conn.execute('SELECT * FROM budgets WHERE id=?', (cur.lastrowid,)).fetchone()
        return jsonify(dict(item)), 201
    finally:
        conn.close()


@app.route('/api/budget/<int:item_id>', methods=['DELETE'])
@login_required
def delete_budget_item(item_id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM budgets WHERE id=?', (item_id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


# ══════════════════════════════════════════════
# PACKING CHECKLIST APIs
# ══════════════════════════════════════════════

@app.route('/api/trips/<int:trip_id>/packing', methods=['GET'])
@login_required
def get_packing(trip_id):
    conn = get_db()
    try:
        items = conn.execute(
            'SELECT * FROM packing_items WHERE trip_id=? ORDER BY category, item_name',
            (trip_id,)
        ).fetchall()
        return jsonify([dict(i) for i in items])
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>/packing', methods=['POST'])
@login_required
def add_packing_item(trip_id):
    data = request.json
    conn = get_db()
    try:
        cur = conn.execute(
            'INSERT INTO packing_items (trip_id, category, item_name, quantity) VALUES (?,?,?,?)',
            (trip_id, data.get('category', 'general'), data.get('item_name'), data.get('quantity', 1))
        )
        conn.commit()
        item = conn.execute('SELECT * FROM packing_items WHERE id=?', (cur.lastrowid,)).fetchone()
        return jsonify(dict(item)), 201
    finally:
        conn.close()


@app.route('/api/packing/<int:item_id>/toggle', methods=['PUT'])
@login_required
def toggle_packing(item_id):
    conn = get_db()
    try:
        item = conn.execute('SELECT is_packed FROM packing_items WHERE id=?', (item_id,)).fetchone()
        conn.execute('UPDATE packing_items SET is_packed=? WHERE id=?', (0 if item['is_packed'] else 1, item_id))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/packing/<int:item_id>', methods=['DELETE'])
@login_required
def delete_packing_item(item_id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM packing_items WHERE id=?', (item_id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>/packing/reset', methods=['POST'])
@login_required
def reset_packing(trip_id):
    conn = get_db()
    try:
        conn.execute('UPDATE packing_items SET is_packed=0 WHERE trip_id=?', (trip_id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


# ══════════════════════════════════════════════
# NOTES / JOURNAL APIs
# ══════════════════════════════════════════════

@app.route('/api/trips/<int:trip_id>/notes', methods=['GET'])
@login_required
def get_notes(trip_id):
    conn = get_db()
    try:
        notes = conn.execute(
            'SELECT * FROM notes WHERE trip_id=? AND user_id=? ORDER BY trip_day, created_at DESC',
            (trip_id, current_user_id())
        ).fetchall()
        return jsonify([dict(n) for n in notes])
    finally:
        conn.close()


@app.route('/api/trips/<int:trip_id>/notes', methods=['POST'])
@login_required
def add_note(trip_id):
    data = request.json
    conn = get_db()
    try:
        cur = conn.execute(
            'INSERT INTO notes (trip_id, user_id, title, content, trip_day, mood) VALUES (?,?,?,?,?,?)',
            (trip_id, current_user_id(), data.get('title', ''), data.get('content'),
             data.get('trip_day', 1), data.get('mood', 'happy'))
        )
        conn.commit()
        note = conn.execute('SELECT * FROM notes WHERE id=?', (cur.lastrowid,)).fetchone()
        return jsonify(dict(note)), 201
    finally:
        conn.close()


@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    data = request.json
    conn = get_db()
    try:
        conn.execute(
            'UPDATE notes SET title=?, content=?, trip_day=?, mood=?, updated_at=? WHERE id=? AND user_id=?',
            (data.get('title'), data.get('content'), data.get('trip_day', 1),
             data.get('mood', 'happy'), datetime.now().isoformat(), note_id, current_user_id())
        )
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM notes WHERE id=? AND user_id=?', (note_id, current_user_id()))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


# ══════════════════════════════════════════════
# DASHBOARD STATS API
# ══════════════════════════════════════════════

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    uid = current_user_id()
    conn = get_db()
    try:
        total_trips = conn.execute('SELECT COUNT(*) as c FROM trips WHERE user_id=?', (uid,)).fetchone()['c']
        total_cities = conn.execute(
            'SELECT COUNT(*) as c FROM trip_stops ts JOIN trips t ON ts.trip_id=t.id WHERE t.user_id=?', (uid,)
        ).fetchone()['c']
        total_spent = conn.execute(
            'SELECT COALESCE(SUM(b.amount),0) as s FROM budgets b JOIN trips t ON b.trip_id=t.id WHERE t.user_id=?', (uid,)
        ).fetchone()['s']
        upcoming = conn.execute(
            "SELECT * FROM trips WHERE user_id=? AND start_date >= date('now') ORDER BY start_date LIMIT 3", (uid,)
        ).fetchall()
        recent = conn.execute(
            'SELECT * FROM trips WHERE user_id=? ORDER BY created_at DESC LIMIT 6', (uid,)
        ).fetchall()

        return jsonify({
            'total_trips': total_trips,
            'total_cities': total_cities,
            'total_spent': total_spent,
            'upcoming_trips': [dict(t) for t in upcoming],
            'recent_trips': [dict(t) for t in recent]
        })
    finally:
        conn.close()


# ══════════════════════════════════════════════
# AI PLANNER API
# ══════════════════════════════════════════════

def generate_ai_itinerary(destination, days, style, budget_level):
    # Mock AI logic - procedural generation of a smart-looking itinerary
    styles = {
        'adventure': ['Hiking', 'Zip-lining', 'Scuba Diving', 'Mountain Biking', 'Explore Caves', 'Jeep Safari'],
        'cultural': ['Museum Tour', 'Historic Temple Visit', 'Local Art Gallery', 'Traditional Dance Show', 'Castle Tour', 'Cooking Class'],
        'relaxing': ['Beach Day', 'Spa & Massage', 'Sunset Cruise', 'Yoga Session', 'Hot Springs', 'Botanical Garden'],
        'foodie': ['Street Food Tour', 'Wine Tasting', 'Fine Dining', 'Local Market Visit', 'Cheese & Farm Tour', 'Brewery Tour'],
        'nightlife': ['Club Hopping', 'Rooftop Bar', 'Live Music Venue', 'Night Market', 'Casino Night', 'Pub Crawl']
    }
    
    general_morning = ['Breakfast at a local cafe', 'Morning walk in the city center', 'Coffee and pastry tasting']
    general_afternoon = ['Lunch at a popular local spot', 'Sightseeing around the main square', 'Shopping at the local district']
    general_evening = ['Dinner with a view', 'Evening stroll', 'Sunset photography']
    
    selected_style = styles.get(style, styles['relaxing'])
    
    # Set expense multiplier based on budget level
    mult = 1.0
    if budget_level == 'budget':
        mult = 0.5
    elif budget_level == 'luxury':
        mult = 3.0

    activities = []
    current_date = datetime.now() + timedelta(days=30) # Default start 30 days from now
    
    for day in range(1, days + 1):
        day_date = (current_date + timedelta(days=day-1)).strftime('%Y-%m-%d')
        
        # Morning
        activities.append({
            'name': random.choice(general_morning),
            'category': 'food',
            'date': day_date,
            'time': '09:00',
            'duration_hours': 1.5,
            'cost': int(random.randint(200, 600) * mult),
            'notes': 'Start the day right!'
        })
        activities.append({
            'name': random.choice(selected_style),
            'category': 'sightseeing',
            'date': day_date,
            'time': '11:00',
            'duration_hours': 2.5,
            'cost': int(random.randint(800, 2500) * mult),
            'notes': f'Main morning activity for {style} lovers.'
        })
        
        # Afternoon
        activities.append({
            'name': random.choice(general_afternoon),
            'category': 'food',
            'date': day_date,
            'time': '14:00',
            'duration_hours': 1.5,
            'cost': int(random.randint(400, 1500) * mult),
            'notes': 'Refuel with some good food.'
        })
        activities.append({
            'name': random.choice(selected_style),
            'category': 'sightseeing',
            'date': day_date,
            'time': '16:00',
            'duration_hours': 2.0,
            'cost': int(random.randint(600, 2000) * mult),
            'notes': 'Afternoon adventure.'
        })
        
        # Evening
        activities.append({
            'name': random.choice(general_evening),
            'category': 'food',
            'date': day_date,
            'time': '19:30',
            'duration_hours': 2.0,
            'cost': int(random.randint(800, 3500) * mult),
            'notes': 'Enjoy the evening.'
        })

    return activities


@app.route('/api/ai/plan', methods=['POST'])
@login_required
def ai_plan_trip():
    data = request.json
    destination = data.get('destination', 'Unknown City')
    days = int(data.get('days', 3))
    style = data.get('style', 'relaxing')
    budget_level = data.get('budget_level', 'medium')
    total_budget_input = int(data.get('total_budget', 1000))
    
    start_date = data.get('start_date')
    if not start_date:
        start_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=days-1)).strftime('%Y-%m-%d')

    uid = current_user_id()
    share_token = uuid.uuid4().hex
    conn = get_db()
    try:
        # Create Trip
        title = f"{style.capitalize()} Trip to {destination}"
        desc = f"An AI-generated {days}-day {style} itinerary for {destination}."
        cur = conn.execute(
            '''INSERT INTO trips (user_id, title, description, start_date, end_date, total_budget, status, share_token)
               VALUES (?,?,?,?,?,?,?,?)''',
            (uid, title, desc, start_date, end_date, total_budget_input, 'planning', share_token)
        )
        trip_id = cur.lastrowid
        
        # Create Stop
        city = destination.split(',')[0] if ',' in destination else destination
        conn.execute(
            'INSERT INTO trip_stops (trip_id, city, country, arrival_date, departure_date, order_index) VALUES (?,?,?,?,?,?)',
            (trip_id, city, destination, start_date, end_date, 0)
        )
        stop_id = cur.lastrowid # We might need a better way to get stop id, actually let's fetch it:
        stop_id = conn.execute('SELECT id FROM trip_stops WHERE trip_id=?', (trip_id,)).fetchone()['id']
        
        # Generate and insert activities
        activities = generate_ai_itinerary(destination, days, style, budget_level)
        for act in activities:
            # We fix dates if the user provided one
            act_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=activities.index(act) // 5)).strftime('%Y-%m-%d')
            if act_date > end_date:
                act_date = end_date
            
            conn.execute(
                '''INSERT INTO trip_activities (trip_id, stop_id, name, category, date, time, duration_hours, cost, notes)
                   VALUES (?,?,?,?,?,?,?,?,?)''',
                (trip_id, stop_id, act['name'], act['category'], act_date, act['time'], act['duration_hours'], act['cost'], act['notes'])
            )

        # Setup budget multiplier
        mult = 1.0
        if budget_level == 'budget': mult = 0.5
        elif budget_level == 'luxury': mult = 3.0

        # Create realistic fixed budgets for the trip
        conn.execute(
            'INSERT INTO budgets (trip_id, category, amount, currency, notes, date) VALUES (?,?,?,?,?,?)',
            (trip_id, 'hotels', int(random.randint(2000, 8000) * mult * days), 'INR', 'Estimated accommodation', start_date)
        )
        conn.execute(
            'INSERT INTO budgets (trip_id, category, amount, currency, notes, date) VALUES (?,?,?,?,?,?)',
            (trip_id, 'transport', int(random.randint(4000, 15000) * mult), 'INR', 'Estimated flights and local travel', start_date)
        )
        conn.execute(
            'INSERT INTO budgets (trip_id, category, amount, currency, notes, date) VALUES (?,?,?,?,?,?)',
            (trip_id, 'shopping', int(random.randint(1000, 5000) * mult), 'INR', 'Shopping and Souvenirs', start_date)
        )
            
        # Add basic packing items based on style
        packing_items = [
            ('Passport & ID', 'documents', 1),
            ('Phone Charger', 'electronics', 1),
            ('Comfortable Shoes', 'clothing', 1),
            ('Toothbrush', 'toiletries', 1)
        ]
        if style == 'adventure':
            packing_items += [('Hiking Boots', 'clothing', 1), ('Water Bottle', 'general', 1), ('First Aid Kit', 'general', 1)]
        elif style == 'relaxing':
            packing_items += [('Swimwear', 'clothing', 2), ('Sunscreen', 'toiletries', 1), ('Sunglasses', 'clothing', 1)]
            
        for item, cat, qty in packing_items:
            conn.execute(
                'INSERT INTO packing_items (trip_id, category, item_name, quantity) VALUES (?,?,?,?)',
                (trip_id, cat, item, qty)
            )
            
        conn.commit()
        return jsonify({'success': True, 'trip_id': trip_id, 'message': 'AI Itinerary generated successfully!'})
    except Exception as e:
        print("AI generation error:", e)
        return jsonify({'error': 'Failed to generate itinerary.'}), 500
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────
if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        init_db()
    else:
        # Ensure tables exist on restart
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
