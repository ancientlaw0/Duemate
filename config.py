import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this_is_the_key'
    RATELIMIT_DEFAULT = "5 per minute"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'app.db')
    
    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("RESEND_SENDER")

    SMS_GATEWAY_CONFIG = {
    "url": os.getenv("SMS_GATEWAY_URL"),
    "username": os.getenv("SMS_GATEWAY_USER"),
    "password": os.getenv("SMS_GATEWAY_PASS")
    }