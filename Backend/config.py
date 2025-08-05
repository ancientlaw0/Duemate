import os
from dotenv import load_dotenv

# # This always points to root of DUEMATE project
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# load_dotenv(os.path.join(project_root, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this_is_the_key'
    RATELIMIT_DEFAULT = "50000 per minute"
    
    # Make sure DB path is absolute and consistent
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'app.db')
    
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    RESEND_SENDER = os.getenv("RESEND_SENDER")

    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-flask-secret")
    JWT_TOKEN_LOCATION = ["headers"] 
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    SMS_GATEWAY_CONFIG = {
        "url": os.getenv("SMS_GATEWAY_URL"),
        "username": os.getenv("SMS_GATEWAY_USER"),
        "password": os.getenv("SMS_GATEWAY_PASS")
    }