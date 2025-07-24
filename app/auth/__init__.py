from flask import Blueprint


bp = Blueprint('/api/auth', __name__)


from app.auth import routes