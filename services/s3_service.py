import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

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
    Uploads a file to AWS S3.

    Args:
        local_file_path: Path of file on local machine.
        s3_folder: uploads or reports

    Returns:
        S3 URL if successful, otherwise None.
    """

    filename = os.path.basename(local_file_path)

    s3_key = f"{s3_folder}/{filename}"

    try:

        s3.upload_file(
            local_file_path,
            BUCKET_NAME,
            s3_key
        )

        url = (
            f"https://{BUCKET_NAME}.s3."
            f"{os.getenv('AWS_REGION')}.amazonaws.com/"
            f"{s3_key}"
        )

        return url

    except ClientError as e:

        print("S3 Upload Error:", e)

        return None