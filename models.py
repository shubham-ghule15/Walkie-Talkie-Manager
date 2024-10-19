# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    """Returns the current time in IST."""
    return datetime.now(IST)

class WalkieTalkie(db.Model):
    __tablename__ = 'walkie_talkies'
    id = db.Column(db.Integer, primary_key=True)
    # Removed 'channel' field to support multiple channels
    is_lent = db.Column(db.Boolean, default=False)
    current_holder = db.Column(db.String(100), nullable=True)
    is_charged = db.Column(db.Boolean, default=False)  # Default is now False (discharged)
    rental_history = db.relationship('Rental', backref='walkie_talkie', lazy=True)
    channels = db.relationship('Channel', backref='walkie_talkie', lazy=True, cascade="all, delete-orphan")

class Channel(db.Model):
    __tablename__ = 'channels'
    id = db.Column(db.Integer, primary_key=True)
    channel_number = db.Column(db.Integer, nullable=False)
    walkie_talkie_id = db.Column(db.Integer, db.ForeignKey('walkie_talkies.id'), nullable=False)
    # Ensure unique channel numbers per walkie-talkie
    __table_args__ = (db.UniqueConstraint('walkie_talkie_id', 'channel_number', name='_walkie_channel_uc'),)

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    rental_history = db.relationship('Rental', backref='department', lazy=True)

class Rental(db.Model):
    __tablename__ = 'rentals'
    id = db.Column(db.Integer, primary_key=True)
    walkie_talkie_id = db.Column(db.Integer, db.ForeignKey('walkie_talkies.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    lend_time = db.Column(db.DateTime, default=get_ist_now, nullable=False)
    return_time = db.Column(db.DateTime, nullable=True)
