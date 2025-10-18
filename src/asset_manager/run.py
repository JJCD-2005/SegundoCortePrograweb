# src/asset_manager/run.py

import os
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin
from sqlalchemy.exc import IntegrityError
from .forms import SignupForm, LoginForm, AssetForm
from . import models # Import only the module to avoid circular dependencies in function scope
from sqlalchemy import select

# --- 1. APPLICATION AND DATABASE CONFIGURATION ---

app = Flask(__name__)

# Required: SECRET_KEY (Cryptographically secure string)
# IMPORTANT: Load this from a secure environment variable in production!
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_super_secret_key_change_me_12345')

# Database Configuration (PostgreSQL)
DB_USER = os.environ.get('DB_USER', 'postgres_user')
DB_PASS = os.environ.get('DB_PASS', 'postgres_password')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'asset_manager_db')

# Required: PostgreSQL connection format
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
# Required: SQLALCHEMY_TRACK_MODIFICATIONS = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
models.db = db # Inject the db instance into models.py

# --- 2. FLASK-LOGIN CONFIGURATION ---

login_manager = LoginManager()
login_manager.init_app(app)

# Required: login_manager.login_view configuration
login_manager.login_view = 'login'

# Required: Implement user_loader callback
@login_manager.user_loader
def load_user(user_id):
    # Use get_by_id static method from User model
    return models.User.get_by_id(int(user_id))

# --- Security Function ---
# Required: Secure URL Redirection validation (parameter 'next')
def is_safe_url(target):
    """Checks if the redirect URL is safe (same application/domain)."""
    # Get the URL of the application's host
    ref_url = urlparse(request.host_url)
    # Join the host URL with the target path and parse it
    target_url = urlparse(urljoin(request.host_url, target))
    
    # Check if the scheme is http/https and the network location is the same
    return target_url.scheme in ('http', 'https') and ref_url.netloc == target_url.netloc

# --- 3. PUBLIC ROUTES (Without authentication) ---

# Required 1: Homepage (/) - Shows list of principal entities
@app.route('/')
def index():
    """Displays the list of all assets."""
    assets = models.Asset.get_all() # Required: get_all() method
    return render_template('index.html', assets=assets)

# Required 2: Detail View (/asset/<slug>/)
@app.route('/asset/<slug>/')
def asset_view(slug):
    """Displays the individual record by slug."""
    asset = models.Asset.get_by_slug(slug) # Required: get_by_slug() method
    
    # Required: Return 404 if record does not exist
    if not asset:
        abort(404) 
        
    return render_template('asset_view.html', asset=asset)

# Required 4: Signup Route (/signup/)
@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    """Allows new user registration."""
    # Required: Redirect authenticated users to home
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = SignupForm()
    if form.validate_on_submit():
        
        # Required: Check for duplicate email and display error
        if models.User.get_by_email(form.email.data): # Uses get_by_email static method
            flash('Email address already exists. Please log in.', 'error')
            return redirect(url_for('signup'))
        
        new_user = models.User(username=form.username.data, email=form.email.data)
        # Required: Hash password before storing (uses set_password internally)
        new_user.set_password(form.password.data) 

        try:
            new_user.save() # Uses save() method
            
            # Required: Auto-login after successful registration
            login_user(new_user)
            flash('Account created successfully! Welcome.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {e}', 'error')

    return render_template('signup_form.html', form=form)

# Required 3: Login Route (/login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Allows user login."""
    # Required: Redirect authenticated users to home
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = models.User.get_by_email(form.email.data)
        
        # Required: Validate credentials using check_password(password)
        if user and user.check_password(form.password.data):
            # Required: Support "remember me"
            login_user(user, remember=form.remember_me.data)
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Required: Handle 'next' parameter with security validation (urlparse)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('login_form.html', form=form)

# Required 5: Logout (/logout)
@app.route('/logout')
def logout():
    """Logs out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    # Required: Redirect to home page
    return redirect(url_for('index'))

# --- 4. PROTECTED ROUTES (@login_required) ---

# Required 6: Create Record (Asset)
@app.route('/admin/asset/new', methods=['GET', 'POST'])
# Required: @login_required decorator
@login_required 
def create_asset():
    """Allows authenticated users to create a new asset."""
    form = AssetForm()
    if form.validate_on_submit():
        # Create new record associated with current_user.id
        new_asset = models.Asset(
            name=form.name.data,
            serial_number=form.serial_number.data,
            description=form.description.data,
            user_id=current_user.id # Associate with current user
        )
        
        try:
            # Required: Persist record with automatic slug generation and error handling
            new_asset.save()
            flash('Asset created successfully!', 'success')
            # Required: Redirect after successful creation
            return redirect(url_for('asset_view', slug=new_asset.slug))
        except IntegrityError:
            # Required: Handle IntegrityError
            db.session.rollback()
            flash('Error: The asset name (for slug) or serial number might be a duplicate.', 'error')
        except ValueError as e:
            # Handles serial number duplication specifically raised in models.py
            flash(f'Error: {e}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {e}', 'error')

    return render_template('admin/asset_form.html', form=form, title='Create New Asset')

# --- 5. ERROR HANDLERS ---

# Required: 404 Error handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# --- 6. ENTRY POINT ---
if __name__ == '__main__':
    # Ensure db.create_all() is within the application context
    with app.app_context():
        # Ensure models are loaded before creating tables
        from . import models 
        db.create_all()
        print("Database tables created!")
    
    # Run the application (using debug=True is okay for development)
    app.run(debug=True)