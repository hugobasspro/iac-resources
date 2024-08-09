from dataclasses import replace
from obs import ObsClient
import sys
import os


def upload_assets(obs_client, bucket_name, local_folder) -> bool:
    """
    Upload assets to the specified bucket.

    Parameters:
    obs_client (ObsClient): The OBS client instance.
    bucket_name (str): The name of the bucket to upload assets to.
    folder (str): The local directory containing the assets to upload.

    Returns:
    bool: True if all assets were uploaded successfully, False otherwise.
    """
    success = True
    for root, dirs, files in os.walk(local_folder):
        print(dirs)
        for filename in files:
            file_path = os.path.join(root, filename)
            object_key = os.path.relpath(file_path, local_folder)
            object_key = object_key.replace("\\","/")
            try:
                print(f"Uploading {file_path} to {bucket_name}/{object_key}...")
                response = obs_client.putFile(bucketName=bucket_name, objectKey=object_key, file_path=file_path)

                if response.status < 300:
                    print(f"Uploaded {file_path} to {bucket_name}/{object_key} successfully.")
                else:
                    print(f"Error: Unable to upload {file_path} to {bucket_name}/{object_key}. Status code: {response.status}")
                    success = False
            except Exception as e:
                print(f"Exception occurred while uploading {file_path} to {bucket_name}/{object_key}: {e}")
                success = False
    return success

def main(bucket_name, access_key_id, secret_access_key, region, folder) -> bool:
    """
    Main function to upload assets to the specified bucket.

    Parameters:
    bucket_name (str): The name of the bucket to upload assets to.
    access_key_id (str): The access key ID for the OBS account.
    secret_access_key (str): The secret access key for the OBS account.
    server (str): The endpoint URL for the OBS service.

    Returns:
    bool: True if all assets were uploaded successfully, False otherwise.
    """
    obs_client = ObsClient(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        server="https://obs."+region+".myhuaweicloud.com"
    )
    #folder = "/"
    return upload_assets(obs_client, bucket_name, folder)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python obs-upload-assets.py <bucket_name> <access_key_id> <secret_access_key> <region> <folder>")
        sys.exit(1)

    bucket_name, access_key_id, secret_access_key, region, folder = sys.argv[1:]

    if main(bucket_name, access_key_id, secret_access_key, region, folder):
        print(f"All assets from '/' uploaded successfully to bucket '{bucket_name}'.")
    else:
        print(f"Failed to upload some or all assets from '/' to bucket '{bucket_name}'.")