from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange

from . import models 

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = models.User.get_by_email(email.data)
        if user is not None:
            raise ValidationError('This email is already registered.')

# Renombrado a AssetForm
class AssetForm(FlaskForm):
    name = StringField('Asset Name / ID', validators=[DataRequired()]) 
    value = DecimalField('Acquisition/Book Value', validators=[DataRequired(), NumberRange(min=0)]) 
    description = TextAreaField('Description and Location', validators=[DataRequired()])
    submit = SubmitField('Register Asset')