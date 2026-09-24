import os
import traceback
import boto3
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")


def upload_file(local_file_path, s3_folder):
    """
    Upload a file to AWS S3.

    Args:
        local_file_path: Local file path
        s3_folder: Folder inside S3 bucket (e.g. uploads)

    Returns:
        S3 URL if successful, otherwise None
    """

    filename = os.path.basename(local_file_path)
    s3_key = f"{s3_folder}/{filename}"

    try:
        print("========== S3 DEBUG ==========")
        print("Bucket:", BUCKET_NAME)
        print("Region:", os.getenv("AWS_REGION"))
        print("File:", local_file_path)
        print("S3 Key:", s3_key)
        print("==============================")

        s3.upload_file(
            local_file_path,
            BUCKET_NAME,
            s3_key
        )

        print("✅ File uploaded successfully!")

        url = (
            f"https://{BUCKET_NAME}.s3."
            f"{os.getenv('AWS_REGION')}.amazonaws.com/"
            f"{s3_key}"
        )

        print("S3 URL:", url)

        return url

    except Exception as e:
        print("\n========== S3 UPLOAD ERROR ==========")
        print("Exception Type:", type(e).__name__)
        print("Exception:", str(e))
        traceback.print_exc()
        print("=====================================\n")

        return None