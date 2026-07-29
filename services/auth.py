from database.models import User
from database.database import db
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

def register_user(form):
    # Get data from the registration form
    full_name = form["full_name"]
    email = form["email"]
    password = form["password"]
    confirm_password = form["confirm_password"]
    role = form["role"]

    # Check if passwords match
    if password != confirm_password:
        return " Passwords do not match."

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return " Email is already registered."

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create new user
    new_user = User(
        full_name=full_name,
        email=email,
        password=hashed_password,
        role=role
    )

    # Save user to database
    db.session.add(new_user)
    db.session.commit()

    return "Registration Successful!"

def login_user(form):

    email = form["email"]
    password = form["password"]

    user = User.query.filter_by(email=email).first()

    if not user:
        return None, "Email not found"

    if not check_password_hash(user.password, password):
        return None, "Incorrect password"

    return user, "Login Successful"