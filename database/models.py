from database.database import db
from datetime import datetime


# -----------------------------
# User Model
# -----------------------------
class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        nullable=False
    )

    # Relationship
    reviews = db.relationship(
        "Review",
        backref="user",
        lazy=True
    )


# -----------------------------
# Review Model
# -----------------------------
class Review(db.Model):

    __tablename__ = "reviews"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    python_file_url = db.Column(
        db.String(500)
    )

    pdf_url = db.Column(
        db.String(500)
    )

    review_data = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )