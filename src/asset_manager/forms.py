# src/asset_manager/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError
from email_validator import validate_email, EmailNotValidError

# --- Validator personalizado para email-validator ---
def validate_email_format(form, field):
    """Validador que utiliza la librería email-validator."""
    try:
        validate_email(field.data, check_deliverability=False) 
    except EmailNotValidError as e:
        raise ValidationError(str(e))

# --- Formularios de Autenticación ---

# Requisito: SignupForm
class SignupForm(FlaskForm):
    """Formulario para el registro de nuevos usuarios."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'), 
        Length(min=3, max=80, message='Username must be between 3 and 80 characters.')
    ])
    
    # Requisito: email (StringField con validadores DataRequired, Email)
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'), 
        validate_email_format
    ])
    
    # Requisito: password (PasswordField con validador DataRequired)
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    
    submit = SubmitField('Register Account')

# Requisito: LoginForm
class LoginForm(FlaskForm):
    """Formulario para el inicio de sesión."""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    # Requisito: remember_me
    remember_me = BooleanField('Remember Me')
    
    submit = SubmitField('Log In')

# --- Formulario de Entidad Principal (AssetForm) ---

# Requisito: Formulario de Entidad Principal
class AssetForm(FlaskForm):
    """Formulario para crear activos."""
    # Requisito: StringField con validador DataRequired y Length
    name = StringField('Asset Name', validators=[
        DataRequired(message='Name is required.'),
        Length(min=5, max=100, message='Name must be 5-100 characters.')
    ])
    
    serial_number = StringField('Serial Number', validators=[
        DataRequired(message='Serial number is required.'),
        Length(max=50, message='Serial number cannot exceed 50 characters.')
    ])
    
    # Requisito: TextAreaField
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required.'),
        Length(min=10, message='Description must be at least 10 characters.')
    ])
    
    submit = SubmitField('Save Asset')