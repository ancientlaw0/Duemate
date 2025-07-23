from app import db
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from flask import current_app

class User(UserMixin,db.Model):
    Userid:so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(200),index = True,unique=True)
    phone_number : so.Mapped[int] = so.mapped_column(sa.INT, unique = True, nullable = False)

