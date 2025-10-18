# src/asset_manager/models.py

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
from python_slugify import slugify
from sqlalchemy import select

# db se inyectará desde run.py
db = None 

# --- MODELO USER (Obligatorio) ---

class User(db.Model, UserMixin):
    # Campos mínimos requeridos
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False) # name o username
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Relación 1:N con Asset (assets es el backref definido en el modelo Asset)
    assets = db.relationship('Asset', backref='owner', lazy='dynamic') 

    # Requisito: set_password(password)
    def set_password(self, password):
        """Hashear y almacenar contraseña usando Werkzeug"""
        self.password_hash = generate_password_hash(password)

    # Requisito: check_password(password)
    def check_password(self, password):
        """Verificar contraseña contra el hash almacenado"""
        return check_password_hash(self.password_hash, password)

    # Requisito: save()
    def save(self):
        """Persistir usuario en base de datos"""
        db.session.add(self)
        db.session.commit()
        
    # Requisito: get_by_id(id) (Método estático)
    @staticmethod
    def get_by_id(id):
        """Obtener usuario por ID"""
        return db.session.get(User, id)
    
    # Requisito: get_by_email(email) (Método estático)
    @staticmethod
    def get_by_email(email):
        """Obtener usuario por email"""
        return db.session.scalar(select(User).where(User.email == email))

    def __repr__(self):
        return f'<User {self.username}>'

# --- MODELO ASSET (Entidad Principal Obligatoria) ---

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Requisito: Foreign Key al modelo User con CASCADE delete
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    # Campos relevantes al dominio
    name = db.Column(db.String(120), nullable=False) 
    serial_number = db.Column(db.String(120), unique=True, nullable=False) 
    
    # Requisito: String largo para contenido
    description = db.Column(db.Text, nullable=False) 

    # Requisito: slug (String, Unique, Not Null)
    slug = db.Column(db.String(150), unique=True, nullable=False) 
    
    created_at = db.Column(db.DateTime, default=db.func.now())

    # Requisito: save() con generación automática de slug y manejo de duplicados/errores
    def save(self):
        """
        Persists the asset in the database. Generates a unique slug automatically.
        Handles IntegrityError for slug and serial_number duplication.
        """
        base_slug = slugify(self.name)
        
        counter = 0
        while True:
            current_slug = f"{base_slug}-{counter}" if counter > 0 else base_slug
            self.slug = current_slug
            
            db.session.add(self)
            
            try:
                # Intenta hacer commit
                db.session.commit()
                return True # Éxito
            except IntegrityError:
                db.session.rollback() # Revierte la sesión
                
                # Manejo de slugs duplicados
                if Asset.query.filter_by(slug=current_slug).first():
                    counter += 1
                    continue # Intenta el siguiente slug (ej. asset-1, asset-2)
                
                # Manejo de serial_number duplicado (Error de negocio)
                if Asset.query.filter_by(serial_number=self.serial_number).first():
                    # Capturar excepciones IntegrityError para manejo de duplicados
                    raise ValueError("Serial number already exists. Please use a unique serial number.")
                
                # Si es otro IntegrityError no esperado
                raise 

    # Requisito: public_url()
    def public_url(self):
        """Genera la URL para ver el registro"""
        from flask import url_for # Importamos localmente para evitar dependencia circular
        return url_for('asset_view', slug=self.slug)

    # Requisito: get_by_slug(slug) (Método estático)
    @staticmethod
    def get_by_slug(slug):
        """Obtiene un registro por slug"""
        return db.session.scalar(select(Asset).filter_by(slug=slug))

    # Requisito: get_all() (Método estático)
    @staticmethod
    def get_all():
        """Obtiene todos los registros"""
        return db.session.scalars(select(Asset).order_by(Asset.created_at.desc())).all()

    def __repr__(self):
        return f'<Asset {self.name}>'