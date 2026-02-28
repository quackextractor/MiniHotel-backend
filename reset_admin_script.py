from __init__ import create_app
from database import db, User
import bcrypt

app = create_app()

with app.app_context():
    username = "admin"
    password = "admin"
    
    existing = User.query.filter_by(username=username).first()
    if existing:
        print(f"User {username} exists, resetting password.")
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        existing.password_hash = hashed.decode('utf-8')
    else:
        print(f"Creating user {username}...")
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(username=username, password_hash=hashed.decode('utf-8'))
        db.session.add(new_user)
    
    db.session.commit()
    print(f"User {username} password is now '{password}'.")
