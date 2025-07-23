from flask import request, session ,  jsonify
import sqlalchemy as sa
from app import db
from app.auth import bp
from app.models import User
from functools import wraps
from app.auth.forms import MobileLoginForm,EmailLoginForm, OtpForm
from random import randint
from app.utils import send_email,send_SMS, generate_jwt # temp email sending logic
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from app import limiter
from flask_limiter.errors import RateLimitExceeded

def otp_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("otp") or not (session.get("email") or session.get("phone_number")):
            return jsonify({"status": "error","next": session.get("next", "/login/email"), "message": "OTP session invalid"}), 403
        return f(*args, **kwargs)
    return decorated_function

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@bp.before_app_request 
def capture_next_url():
    next_url = request.args.get("next")
    if next_url and is_safe_url(next_url):
        session["next"] = next_url


@bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "status": "error",
        "message": "Too many OTP attempts. Try again later."
    }), 429

@bp.route('/login/email', methods=['GET', 'POST'])
def login_email():
    form = EmailLoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data)
        )

        if not user:
            user = User(email=form.email.data)
            db.session.add(user)
            db.session.commit() # return json here for sucess

        # OTP generation
        otp = str(randint(100000, 999999)) 
        session['otp'] = otp
        session['otp_time'] = datetime.now().isoformat()
        session['email'] = form.email.data
       
        send_email(form.email.data, otp)  # abstract this in util

        return jsonify({
            "status": "success",
            "next": session.get("next", "/verify_otp"),
            "message": f"OTP sent to {form.email.data}"
        }), 200

    return jsonify({"status": "fail","next": session.get("next", "/login/email"), "errors": form.errors}), 400

@bp.route('/login/mobile', methods=['GET', 'POST'])
def login_mobile():
    form = MobileLoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.phone_number == form.phone_number.data)
        )

        if not user:
            user = User(phone_number=form.phone_number.data)
            db.session.add(user)
            db.session.commit() # return json here for sucess

        # OTP generation
        otp = str(randint(100000, 999999)) 
        session['otp'] = otp
        session['otp_time'] = datetime.now().isoformat() 
        session['phone_number'] = form.phone_number.data

       
        send_SMS(form.phone_number.data, otp)  # abstract this in util
        
        return jsonify({
            "status": "success",
            "next": session.get("next", "/verify_otp"),
            "message": f"OTP sent to {form.phone_number.data}"
        }), 200

    return jsonify({"status": "fail","next": session.get("next", "/login/mobile"), "errors": form.errors}), 400


@bp.route('/verify_otp', methods=['POST'])
@otp_required
@limiter.limit("3 per minute")
def verify_otp():
    form = OtpForm()
    if not form.validate_on_submit():
        return jsonify({"status": "error","next": session.get("next", "/login/email"), "message": "Invalid form", "errors": form.errors}), 400

    entered_otp = form.otp.data
    email = session.get("email")
    phone = session.get("phone_number")

    stored_otp = session.get("otp")
    otp_created_time = session.get("otp_time")

    if not otp_created_time:
        return jsonify({"status": "error","next": session.get("next", "/login/email"), "message": "OTP timestamp missing"}), 400

    otp_created_time = datetime.fromisoformat(otp_created_time)
    if datetime.now() - otp_created_time > timedelta(minutes=5):  # 5 min expiry
        session.pop("otp", None)
        session.pop("email", None)
        session.pop("phone_number",None)
        session.pop("otp_time", None)
        return jsonify({"status": "error","next": session.get("next", "/login/email"), "message": "OTP expired"}), 403

    if not (email or phone) or not stored_otp:
        return jsonify({"status": "error","next": session.get("next", "/login/email"), "message": "Session expired or invalid"}), 400

    if entered_otp != stored_otp:
        session.pop("otp", None)
        session.pop("email", None)
        session.pop("phone_number",None)
        session.pop("otp_time", None)
        return jsonify({"status": "error","next": session.get("next", "/login/email"), "message": "Invalid OTP"}), 401

    if email:
        user = db.session.scalar(sa.select(User).where(User.email == email))
    elif phone:
        user = db.session.scalar(sa.select(User).where(User.phone_number == phone))
    else:
        return jsonify({"status": "error","next": session.get("next", "/login/email"), "message": "User not found"}), 404

    token = generate_jwt(user)

    session.pop("otp", None)
    session.pop("email", None)
    session.pop("phone_number",None)

    return jsonify({
        "status": "success",
        "next": session.get("next", "/dashboard"),
        "access_token": token
    }), 200

