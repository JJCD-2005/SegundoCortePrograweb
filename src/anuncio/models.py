import os
import re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

# IMPORTAMOS la instancia de db desde __init__.py
from . import db 

# FUNCIÓN MANUAL DE SLUGIFY
def _simple_slugify(text):
    """Convierte texto a un slug simple (solo minúsculas, guiones)."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text) 
    text = re.sub(r'[-\s]+', '-', text)  
    return text.strip('-')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # CORRECCIÓN CRÍTICA: Aumentar a 256 para evitar StringDataRightTruncation
    password_hash = db.Column(db.String(256), nullable=False) 
    
    # Relación cambiada a 'assets' (activos)
    assets = db.relationship('Asset', backref='author', lazy='dynamic', cascade="all, delete-orphan") 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save(self):
        db.session.add(self)
        db.session.commit()
    
    @staticmethod
    def get_by_email(email):
        return db.session.scalar(select(User).where(User.email == email))

    @staticmethod
    def get_by_id(id):
        return db.session.get(User, id)

# Clase de Activo (Asset)
class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False) 
    description = db.Column(db.Text, nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False) 
    slug = db.Column(db.String(128), unique=True, nullable=False) 
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def _generate_unique_slug(self, name): 
        base_slug = _simple_slugify(name)
        slug = base_slug
        counter = 1
        
        # Buscamos por slug
        while db.session.scalar(select(Asset).where(Asset.slug == slug)):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self):
        if not self.slug:
            self.slug = self._generate_unique_slug(self.name)
        
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            self.slug = self._generate_unique_slug(self.name) 
            db.session.add(self)
            db.session.commit()

    @staticmethod
    def get_by_slug(slug):
        return db.session.scalar(select(Asset).where(Asset.slug == slug))

    @staticmethod
    def get_all():
        return db.session.scalars(select(Asset).order_by(Asset.timestamp.desc())).all()

    def public_url(self):
        from flask import url_for
        # Referencia la ruta 'asset_view'
        return url_for('asset_view', slug=self.slug)

def load_user(user_id):
    return User.get_by_id(int(user_id))