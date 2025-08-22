import os
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError 
from dotenv import load_dotenv
load_dotenv()

def upload_folder_to_gcs(local_folder_path: str, gcs_bucket_name: str, gcs_base_path: str, project_id: str):
    try:
        client = storage.Client(project=project_id)
        bucket = client.bucket(gcs_bucket_name)

        if not os.path.exists(local_folder_path):
            print(f"Local folder does not exist: {local_folder_path}")
            return

        counter = 1
        for root, _, files in os.walk(local_folder_path):
            if not files:
                print(f"No files found in: {root}")
            for file_name in files:
                local_file_path = os.path.join(root, file_name)

                # Maintain subdirectory structure inside GCS
                relative_path = os.path.relpath(local_file_path, local_folder_path)
                gcs_blob_path = os.path.join(gcs_base_path, relative_path).replace("\\", "/")

                try:
                    blob = bucket.blob(gcs_blob_path)
                    blob.upload_from_filename(local_file_path)
                    print(f"[{counter}] Uploaded: '{file_name}' → gs://{gcs_bucket_name}/{gcs_blob_path}")
                    counter += 1
                except GoogleAPIError as e:
                    print(f"Failed to upload '{file_name}': {e}")

        if counter == 1:
            print("No files were uploaded. Please check the folder and GCS config.")

    except Exception as e:
        print(f"Error during upload process: {e}")

# ---- Usage ----
upload_folder_to_gcs(
    local_folder_path=r"C:\Users\milan.ajudiya\Desktop\ccc_ChromaDB - Copy\ccc_ChromaDB\multi_tool_agent\schemas",
    gcs_bucket_name= os.getenv("GOOGLE_BUCKET"),
    gcs_base_path=os.getenv("GOOGLE_SCHEMA_PATH"),
    project_id=os.getenv("BQ_PROJECT_ID")
)
