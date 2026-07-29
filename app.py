import os
import json

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from config import Config
from database.database import db
from database.models import Review
from services.auth import register_user, login_user
from services.analyzer import read_python_file
from services.ai_service import review_python_code
from services.pdf_service import generate_pdf
from flask import send_file

from services.s3_service import upload_file
app = Flask(__name__)
app.secret_key = "codelens_secret_key"

app.config.from_object(Config)

db.init_app(app)


# -----------------------------
# Home
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        message = register_user(request.form)

        return render_template(
            "register.html",
            message=message
        )

    return render_template("register.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user, message = login_user(request.form)

        if user:

            session["user_id"] = user.id
            session["user_name"] = user.full_name
            session["role"] = user.role

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            message=message
        )

    return render_template("login.html")


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )


# -----------------------------
#Upload + AI Review
# -----------------------------
# -----------------------------
# Upload + AI Review
# -----------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        file = request.files.get("code_file")

        if file is None:
            return render_template(
                "upload.html",
                message="Please choose a file.",
                message_type="error"
            )

        if file.filename == "":
            return render_template(
                "upload.html",
                message="No file selected.",
                message_type="error"
            )

        if not file.filename.endswith(".py"):
            return render_template(
                "upload.html",
                message="Only Python (.py) files are allowed.",
                message_type="error"
            )

        # Create uploads folder
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        # Save uploaded file locally
        file.save(filepath)

        # Upload Python file to S3
        python_file_url = upload_file(
            filepath,
            "uploads"
        )

        session["python_file_url"] = python_file_url
        session["filename"] = file.filename

        if python_file_url:
            print("\n✅ Python file uploaded successfully!")
            print(python_file_url)
        else:
            print("\n❌ Failed to upload Python file to AWS.")

        # Read uploaded code
        success, code = read_python_file(filepath)

        if not success:
            return render_template(
                "upload.html",
                message=code,
                message_type="error"
            )

        # Generate AI Review
        review = review_python_code(code)

        # -----------------------------
        # Gemini Failed
        # -----------------------------
        if review.get("overall_rating") == "Error":

            return render_template(
                "upload.html",
                message="🤖 AI service is currently busy. Please try again in a few seconds.",
                message_type="error"
            )

        # Store review in session
        session["review"] = review

        # Save review ONLY ONCE
        new_review = Review(
            user_id=session["user_id"],
            filename=file.filename,
            python_file_url=python_file_url,
            review_data=json.dumps(review)
        )

        db.session.add(new_review)
        db.session.commit()

        # Save review id for PDF update
        session["review_id"] = new_review.id

        print("✅ Review saved successfully!")
        print("Review ID:", new_review.id)

        return render_template(
            "report.html",
            code=code,
            review=review
        )

    return render_template("upload.html")
    # -----------------------------
# Logout
# -----------------------------


# -----------------------------
# Download PDF
# -----------------------------
@app.route("/download_report")
def download_report():

    if "review" not in session:
        return redirect(url_for("dashboard"))

    if "review_id" not in session:
        return redirect(url_for("dashboard"))

    # Generate PDF
    pdf = generate_pdf(
        session["review"],
        session["filename"],
        session["user_id"]
    )

    # Upload PDF to AWS S3
    pdf_url = upload_file(
        pdf,
        "reports"
    )

    if pdf_url:

        print("\n✅ PDF uploaded successfully!")
        print(pdf_url)

        # -----------------------------
        # Update existing review
        # -----------------------------
        review = Review.query.get(session["review_id"])

        if review:

            review.pdf_url = pdf_url

            db.session.commit()

            print("✅ Review updated successfully!")

        else:

            print("❌ Review not found.")

    else:

        print("\n❌ PDF upload failed.")

    return send_file(
        pdf,
        as_attachment=True
    )
@app.route("/history")
def history():

    print("========== HISTORY ==========")
    print("Session:", dict(session))

    if "user_id" not in session:
        print("No user in session!")
        return redirect(url_for("login"))

    print("Logged in user:", session["user_id"])

    reviews = Review.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Review.created_at.desc()
    ).all()

    print("Reviews found:", len(reviews))

    for r in reviews:
        print(r.filename)

    return render_template(
        "history.html",
        reviews=reviews
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))
 




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
    