from flask import Flask
from flask_cors import CORS
from database import db
from extensions import limiter
import os
import secrets

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///minihotel.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Secret Key Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    if not app.config['SECRET_KEY']:
        if os.getenv('FLASK_ENV') == 'production':
            raise RuntimeError("SECRET_KEY must be set in production!")
        else:
            print("WARNING: Using generated secret key. Sessions will not persist across restarts.")
            app.config['SECRET_KEY'] = secrets.token_hex(32)
    else:
        pass # The else block is now empty as the assignment is done upfront.

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    limiter.init_app(app)

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.room_routes import room_bp
    from routes.guest_routes import guest_bp
    from routes.booking_routes import booking_bp
    from routes.service_routes import service_bp
    from routes.operations_routes import operations_bp
    from routes.report_routes import report_bp
    from routes.exchange_routes import exchange_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(guest_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(service_bp)
    app.register_blueprint(operations_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(exchange_bp)

    from routes.event_routes import event_bp
    app.register_blueprint(event_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    return app
