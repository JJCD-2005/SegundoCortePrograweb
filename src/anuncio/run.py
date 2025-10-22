import os
from urllib.parse import urlparse, urljoin
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_user, logout_user, login_required 

from . import db, models
from .forms import SignupForm, LoginForm, AssetForm 

# --- 1. APPLICATION AND DATABASE CONFIGURATION ---
def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-very-secret-key-0123456789') 

    # --- CONFIGURACIÓN PARA USAR SQLite (Base de datos local) ---
    # Esto crea un archivo llamado 'app.db' en la carpeta superior del proyecto
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    db_path = os.path.join(basedir, 'app.db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
    
    db.init_app(app) 

    # --- 2. LOGIN MANAGER CONFIGURATION ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login' 

    @login_manager.user_loader
    def load_user(user_id):
        return models.load_user(user_id)

    # --- SOLUCIÓN ERROR JINJA2: 'now' is undefined ---
    @app.context_processor
    def inject_now():
        """Hace que la función now() esté disponible en todas las plantillas Jinja2."""
        return {'now': datetime.utcnow}
    # ----------------------------------------------------

    # --- 3. ROUTES (Adaptadas a ASSET) ---
    def is_safe_url(target):
        ref_url = urlparse(request.host_url)
        target_url = urlparse(urljoin(request.host_url, target))
        return target_url.scheme in ('http', 'https') and \
               ref_url.netloc == target_url.netloc

    @app.route('/')
    def index():
        assets = models.Asset.get_all()
        return render_template('index.html', title='Home', assets=assets)

    # Ruta de vista de activo
    @app.route('/asset/<slug>/')
    def asset_view(slug):
        asset = models.Asset.get_by_slug(slug)
        if asset is None:
            return render_template('404.html', title='Not Found'), 404
        return render_template('asset_view.html', title=asset.name, asset=asset)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated: return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = models.User.get_by_email(form.email.data)
            if user is None or not user.check_password(form.password.data):
                flash('Credenciales inválidas', 'danger')
                return redirect(url_for('login'))
            login_user(user, remember=form.remember_me.data) 
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                return redirect(url_for('index'))
            return redirect(next_page)
        return render_template('login_form.html', title='Acceder', form=form)

    @app.route('/signup/', methods=['GET', 'POST'])
    def signup():
        if current_user.is_authenticated: return redirect(url_for('index'))
        form = SignupForm()
        if form.validate_on_submit():
            if models.User.get_by_email(form.email.data):
                flash('Este email ya está registrado.', 'danger')
                return redirect(url_for('signup'))
            new_user = models.User(name=form.name.data, email=form.email.data)
            new_user.set_password(form.password.data)
            new_user.save()
            login_user(new_user) 
            flash('Registro exitoso. Bienvenido al sistema.', 'success')
            return redirect(url_for('index'))
        return render_template('signup_form.html', title='Registro', form=form)

    @app.route('/logout')
    @login_required 
    def logout():
        logout_user() 
        flash('Sesión cerrada correctamente.', 'info')
        return redirect(url_for('index'))

    # Ruta de registro de activo
    @app.route('/admin/asset/register', methods=['GET', 'POST'])
    @login_required 
    def register_asset():
        form = AssetForm()
        if form.validate_on_submit():
            new_asset = models.Asset(
                user_id=current_user.id, 
                name=form.name.data,
                description=form.description.data,
                value=form.value.data
            )
            new_asset.save()
            flash(f'Activo "{new_asset.name}" registrado con éxito!', 'success')
            return redirect(url_for('asset_view', slug=new_asset.slug))
        return render_template('admin/ad_form.html', title='Registrar Activo', form=form)
        
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Creará el archivo app.db y las tablas user/asset
        db.create_all()
        print("Database tables created!")
    
    app.run(debug=True)