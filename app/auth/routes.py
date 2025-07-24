from flask import request, session ,  jsonify
import sqlalchemy as sa
from pydantic import ValidationError
from app import db
from app.auth import bp
from app.models import User
from functools import wraps
from app.auth.schema import MobileLoginSchema,EmailLoginSchema, OtpSchema
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
            return jsonify({"status": "error", "message": "OTP session invalid"}), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "status": "error",
        "message": "Too many OTP attempts. Try again later."
    }), 429

@bp.route('/login/email', methods=['POST'])
def login_email():
    try:
        
        data = EmailLoginSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({
            "status": "fail", 
            "errors": e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            "status": "fail", 
            "message": "Invalid JSON"
        }), 400

  
    user = db.session.scalar(sa.select(User).where(User.email == data.email))

    if not user:
        user = User(email=data.email)
        db.session.add(user)
        db.session.commit()

    
    otp = str(randint(100000, 999999))
    session['otp'] = otp
    session['otp_time'] = datetime.now().isoformat()
    session['email'] = data.email

    
    try:
        send_email(data.email, otp)
    except Exception as e:
        return jsonify({
            "status": "fail",
            "message": "Failed to send OTP"
        }), 500

    return jsonify({
        "status": "success",
        "message": f"OTP sent to {data.email}"
    }), 200

@bp.route('/login/mobile', methods=['POST'])
def login_mobile():
    try:
       
        data = MobileLoginSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({
            "status": "fail", 
            "errors": e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            "status": "fail", 
            "message": "Invalid JSON"
        }), 400

  
    user = db.session.scalar(sa.select(User).where(User.phone_number == data.phone_number))

    if not user:
        user = User(phone_number=data.phone_number)
        db.session.add(user)
        db.session.commit()

    # probably temporary
    otp = str(randint(100000, 999999))
    session['otp'] = otp
    session['otp_time'] = datetime.now().isoformat()
    session['phone_number'] = data.phone_number

 
    try:
        send_SMS(data.phone_number, otp)
    except Exception as e:
        return jsonify({
            "status": "fail",
            "message": "Failed to send OTP"
        }), 500

    return jsonify({
        "status": "success",
        "message": f"OTP sent to {data.phone_number}"
    }), 200


@bp.route('/verify_otp', methods=['POST'])
@otp_required
@limiter.limit("3 per minute")
def verify_otp():
  
    try:
        data = OtpSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({
            "status": "error", 
            "message": "Invalid input",
            "errors": e.errors()
        }), 400
    except Exception:
        return jsonify({
            "status": "error", 
            "message": "Invalid JSON"
        }), 400

    entered_otp = data.otp
    email = session.get("email")
    phone = session.get("phone_number")
    stored_otp = session.get("otp")
    otp_created_time = session.get("otp_time")

   
    if not otp_created_time:
        return jsonify({"status": "error", "message": "OTP timestamp missing"}), 400

    try:
        otp_created_time = datetime.fromisoformat(otp_created_time)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid OTP timestamp"}), 400

    
    if datetime.now() - otp_created_time > timedelta(minutes=5):
        clear_otp_session()
        return jsonify({"status": "error", "message": "OTP expired"}), 403

   
    if not (email or phone) or not stored_otp:
        return jsonify({"status": "error", "message": "Session expired or invalid"}), 400

   
    if entered_otp != stored_otp:
        clear_otp_session()
        return jsonify({"status": "error", "message": "Invalid OTP"}), 401

   
    user = None
    if email:
        user = db.session.scalar(sa.select(User).where(User.email == email))
    elif phone:
        user = db.session.scalar(sa.select(User).where(User.phone_number == phone))
    
    if not user:
        clear_otp_session()
        return jsonify({"status": "error", "message": "User not found"}), 404

    
    try:
        token = generate_jwt(user)
    except Exception as e:
        return jsonify({"status": "error", "message": "Token generation failed"}), 500

   
    clear_otp_session()

    return jsonify({
        "status": "success",
        "access_token": token,
        "user_id": user.id 
    }), 200


def clear_otp_session():
    """Helper function to clear OTP-related session data"""
    session.pop("otp", None)
    session.pop("email", None)
    session.pop("phone_number", None)
    session.pop("otp_time", None)