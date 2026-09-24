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
import flask

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
# Upload + AI Review
# -----------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        try:

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

            # -------------------------
            # Save locally
            # -------------------------

            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                file.filename
            )

            file.save(filepath)

            print("✅ File saved locally:", filepath)

            # -------------------------
            # Upload to S3
            # -------------------------

            python_file_url = upload_file(
                filepath,
                "uploads"
            )

            print("S3 URL:", python_file_url)

            if python_file_url is None:
                return render_template(
                    "upload.html",
                    message="Failed to upload file to AWS S3.",
                    message_type="error"
                )

            session["python_file_url"] = python_file_url
            session["filename"] = file.filename

            # -------------------------
            # Read File
            # -------------------------

            success, code = read_python_file(filepath)

            if not success:
                return render_template(
                    "upload.html",
                    message=code,
                    message_type="error"
                )

            print("✅ Python file read successfully")

            # -------------------------
            # Gemini Review
            # -------------------------

            review = review_python_code(code)

            print("Gemini Response:", review)

            if review.get("overall_rating") == "Error":

                return render_template(
                    "upload.html",
                    message=review["summary"],
                    message_type="error"
                )

            session["review"] = review

            # -------------------------
            # Save Review
            # -------------------------

            new_review = Review(
                user_id=session["user_id"],
                filename=file.filename,
                python_file_url=python_file_url,
                review_data=json.dumps(review)
            )

            db.session.add(new_review)
            db.session.commit()

            session["review_id"] = new_review.id

            print("✅ Review saved successfully")
            print("Review ID:", new_review.id)

            return render_template(
                "report.html",
                code=code,
                review=review
            )

        except Exception as e:

            db.session.rollback()

            print("\n========== UPLOAD ERROR ==========")
            print(type(e))
            print(e)
            print("==================================\n")

            return render_template(
                "upload.html",
                message=f"Server Error: {e}",
                message_type="error"
            )

    return render_template("upload.html")
  

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

    return flask.send_file(
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
    