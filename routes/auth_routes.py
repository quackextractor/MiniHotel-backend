from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import bcrypt
import jwt
from database import db, User
from utils import token_required, log_audit
from extensions import limiter

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """Check if admin account exists
    ---
    responses:
      200:
        description: Status
    """
    admin_exists = User.query.first() is not None
    return jsonify({'initialized': admin_exists})


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register the initial admin account (only allowed if no users exist)
    ---
    responses:
      201:
        description: User created
      400:
        description: Users already exist
    """
    if User.query.first():
        return jsonify({'message': 'Admin account already exists. Please login.'}), 400

    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400

    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    new_user = User(
        username=data['username'],
        password_hash=hashed_password.decode('utf-8')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    log_audit(new_user.id, "REGISTER", "Initial admin registration")
    
    return jsonify({'message': 'Admin account created successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Login and get token
    ---
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    auth = request.get_json()
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Could not verify', 'WWW-Authenticate': 'Basic realm="Login required!"'}), 401

    user = User.query.filter_by(username=auth.get('username')).first()

    if not user:
        return jsonify({'message': 'User not found'}), 401

    if bcrypt.checkpw(auth.get('password').encode('utf-8'), user.password_hash.encode('utf-8')):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")
        
        log_audit(user.id, "LOGIN", "User logged in")

        return jsonify({'token': token, 'username': user.username})

    return jsonify({'message': 'Invalid password', 'WWW-Authenticate': 'Basic realm="Login required!"'}), 401


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Change user password
    ---
    responses:
      200:
        description: Password changed successfully
      400:
        description: Invalid data or wrong current password
    """
    data = request.get_json()
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'message': 'Missing current or new password'}), 400
        
    if not bcrypt.checkpw(data['current_password'].encode('utf-8'), current_user.password_hash.encode('utf-8')):
         return jsonify({'message': 'Invalid current password'}), 401
         
    hashed_password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt())
    current_user.password_hash = hashed_password.decode('utf-8')
    
    db.session.commit()
    log_audit(current_user.id, "CHANGE_PASSWORD", "User changed password")
    
    return jsonify({'message': 'Password changed successfully'})


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update admin credentials
    ---
    responses:
      200:
        description: Profile updated
    """
    data = request.get_json()
    
    if data.get('password'):
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        current_user.password_hash = hashed_password.decode('utf-8')
        
    if data.get('username'):
        current_user.username = data['username']
        
    db.session.commit()
    log_audit(current_user.id, "UPDATE_PROFILE", "User updated profile")
    
    return jsonify({'message': 'Profile updated successfully'})
