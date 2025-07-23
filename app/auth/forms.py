from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo,Length, Regexp
import sqlalchemy as sa
from app import db
from app.models import User
from flask import current_app

class EmailLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send OTP')

class MobileLoginForm(FlaskForm):
    phone_number = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=10)])
    submit = SubmitField('Send OTP')

class OtpForm(FlaskForm):
    otp = StringField("Enter OTP", validators=[
        DataRequired(),
        Length(min=6, max=6),
        Regexp(r'^\d{6}$', message="OTP must be exactly 6 digits") # enforcement of 6 digits
    ])
    submit = SubmitField("Verify")