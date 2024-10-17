# # app.py
# from flask import Flask
# from models import db

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///walkie_talkie.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SECRET_KEY'] = 'your_secret_key_here'

# db.init_app(app)

# with app.app_context():
#     db.create_all()

# # Import routes
# import routes

# app.py
import os
from flask import Flask
from models import db
from flask_migrate import Migrate


app = Flask(__name__)


# Use DATABASE_URL environment variable if available, else default to SQLite for local development
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///walkie_talkie.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_here')

db.init_app(app)

migrate = Migrate(app, db)


# Remove or comment out db.create_all() if using migrations
# with app.app_context():
#     db.create_all()

# Import routes
import routes

if __name__ == '__app__':
    app.run()