import os

def upload_file(file, app):

    if file.filename == "":
        return False, "Please select a file."

    if not file.filename.endswith(".py"):
        return False, "Only Python (.py) files are allowed."

    upload_folder = os.path.join(
        app.root_path,
        "static",
        "uploads"
    )

    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(
        upload_folder,
        file.filename
    )

    file.save(filepath)

    return True, "File uploaded successfully!"