# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class WalkieTalkie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel = db.Column(db.Integer, nullable=True, default=1)
    is_lent = db.Column(db.Boolean, default=False)
    current_holder = db.Column(db.String(100), nullable=True)
    is_charged = db.Column(db.Boolean, default=False)  # Default is now False (discharged)
    rental_history = db.relationship('Rental', backref='walkie_talkie', lazy=True)

    # Relationship to rentals
    rental_history = db.relationship('Rental', backref='walkie_talkie', lazy=True)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    # Relationship to rentals
    rental_history = db.relationship('Rental', backref='department', lazy=True)

class Rental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    walkie_talkie_id = db.Column(db.Integer, db.ForeignKey('walkie_talkie.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    lend_time = db.Column(db.DateTime, default=datetime.now)
    return_time = db.Column(db.DateTime, nullable=True)
