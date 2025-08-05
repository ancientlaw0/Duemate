from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_jwt_extended import JWTManager

import os
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(project_root, '.env'))


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
limiter = Limiter(key_func=get_remote_address)
login.login_message =('Please log in to access this page.')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    import os
    jwt = JWTManager(app)
    migrate.init_app(app, db)  
    jwt.init_app(app)
    login.init_app(app)
    from app.models import User
    

    @login.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    limiter.init_app(app)


    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp, url_prefix='/api')

    CORS(app,
        resources={r"/*": {"origins": ["http://127.0.0.1:5500"]}},
        allow_headers=["Content-Type", "Authorization"],
        supports_credentials=True,
        methods=["GET", "POST", "PUT","PATCH", "DELETE", "OPTIONS"])
 
    return app




from app import models