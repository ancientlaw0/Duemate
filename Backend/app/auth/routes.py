from flask import request, session ,  jsonify
import sqlalchemy as sa
from pydantic import ValidationError
from app import db
from app.auth import bp
from app.models import User
from functools import wraps
from app.auth.schema import MobileLoginSchema,EmailLoginSchema, OtpSchema
from random import randint
from app.utils import send_email,send_sms#, generate_jwt # temp email sending logic
from datetime import datetime, timedelta
from app import limiter
from flask_limiter.errors import RateLimitExceeded
from flask import render_template
otp_store = {}

# def otp_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not session.get("otp") or not (session.get("email") or session.get("phone_number")):
#             return jsonify({"status": "error", "message": "OTP session invalid"}), 403
#         return f(*args, **kwargs)
#     return decorated_function

def send_otp_email(to_email, otp_code):
    html_body = render_template("otp_email.html", otp=otp_code)
    text_body = f"Your OTP is: {otp_code}"

    send_email(
        to=to_email,
        subject="Duemate Sign In",
        html=html_body,
        text=text_body
    )

def send_otp_sms(to_number, otp_code):
    sms_text = render_template("otp_sms.txt", otp=otp_code)
    
    send_sms(
        to_number=to_number,
        message_text=sms_text
    )

@bp.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    return jsonify({
        "status": "error",
        "message": "Too many OTP attempts. Try again later."
    }), 429
@bp.route('/login', methods=['POST'])
def login():
    json_data = request.get_json()

    if not json_data:
        return jsonify({
            "status": "fail",
            "message": "Invalid JSON or empty request"
        }), 400

    email = json_data.get('email')
    phone_number = json_data.get('phone_number')

    if email:
        try:
            data = EmailLoginSchema(**json_data)
        except ValidationError as e:
            return jsonify({
                "status": "fail",
                "errors": e.errors()
            }), 400

        user = db.session.scalar(sa.select(User).where(User.email == data.email))
        if not user:
            user = User(email=data.email)
            db.session.add(user)
            db.session.commit()

        otp = str(randint(100000, 999999))

        otp_store[data.email] = {
            'otp': otp,
            'time': datetime.now()
        }

        try:
            send_otp_email(data.email, otp)
        except Exception:
            return jsonify({
                "status": "fail",
                "message": "Failed to send OTP"
            }), 500


        return jsonify({
            "status": "success",
            "message": f"OTP sent to {data.email}"
        }), 200

    elif phone_number:
        try:
            data = MobileLoginSchema(**json_data)
        except ValidationError as e:
            return jsonify({
                "status": "fail",
                "errors": e.errors()
            }), 400

        user = db.session.scalar(sa.select(User).where(User.phone_number == data.phone_number))
        if not user:
            user = User(phone_number=data.phone_number)
            db.session.add(user)
            db.session.commit()

        otp = str(randint(100000, 999999))

       
        otp_store[data.phone_number] = {
            'otp': otp,
            'time': datetime.now()
        }

        try:
            send_sms(data.phone_number, otp)
        except Exception:
            return jsonify({
                "status": "fail",
                "message": "Failed to send OTP"
            }), 500

        return jsonify({
            "status": "success",
            "message": f"OTP sent to {data.phone_number}"
        }), 200

    else:
        return jsonify({
            "status": "fail",
            "message": "Invalid input. Provide 'email' or 'phone_number'"
        }), 400


@bp.route('/verify_otp', methods=['POST'])
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

    identifier = data.email or data.phone_number
    entered_otp = data.otp

    if not identifier:
        return jsonify({"status": "error", "message": "Missing email or phone_number"}), 400

    otp_entry = otp_store.get(identifier)

    if not otp_entry:
        return jsonify({"status": "error", "message": "OTP session not found"}), 400

    stored_otp = otp_entry.get('otp')
    otp_created_time = otp_entry.get('time')

    if not otp_created_time:
        otp_store.pop(identifier, None)
        return jsonify({"status": "error", "message": "OTP timestamp missing"}), 400

    if datetime.now() - otp_created_time > timedelta(minutes=5):
        otp_store.pop(identifier, None)
        return jsonify({"status": "error", "message": "OTP expired"}), 403

    if entered_otp != stored_otp:
        otp_store.pop(identifier, None)
        return jsonify({"status": "error", "message": "Invalid OTP"}), 401


    user = None
    if data.email:
        user = db.session.scalar(sa.select(User).where(User.email == data.email))
    elif data.phone_number:
        user = db.session.scalar(sa.select(User).where(User.phone_number == data.phone_number))

    if not user:
        otp_store.pop(identifier, None)
        return jsonify({"status": "error", "message": "User not found"}), 404

    # try:
    #     token = generate_jwt(user)
    # except Exception:
    #     return jsonify({"status": "error", "message": "Token generation failed"}), 500

    otp_store.pop(identifier, None) 

    return jsonify({
        "status": "success",
        # "access_token": token,
        "user_id": user.id
    }), 200
