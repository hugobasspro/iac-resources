from obs import ObsClient
import sys
import json

def set_bucket_acl_to_private_if_needed(obs_client, bucket_name) -> bool:
    """
    Set the bucket ACL to private if it's not already set.

    Parameters:
    obs_client (ObsClie nt): The OBS client instance.
    bucket_name (str): The name of the bucket to check and update.

    Returns:
    bool: True if the ACL was set to private or was already private, False otherwise.
    """
    try:
        acl_response = obs_client.getBucketAcl(bucketName=bucket_name)
        print(acl_response.body)
        if acl_response.status < 300 and acl_response.body.owner and acl_response.body.grants:
            is_private = True
            for grant in acl_response.body.grants:
                if grant.grantee.type != 'CanonicalUser' or grant.permission != 'FULL_CONTROL':
                    is_private = False
                    break
            if not is_private:
                obs_client.setBucketAcl(bucketName=bucket_name, acl='private')
                print("Bucket ACL set to private successfully.")
            else:
                print("Bucket ACL is already private.")
            return True
        else:
            print("Failed to retrieve bucket ACL.")
            return False
    except Exception as e:
        print(f"Exception occurred while setting bucket ACL to private: {e}")
        return False

def is_bucket_private(obs_client, bucket_name) -> bool:
    try:
        acl_response = obs_client.getBucketAcl(bucketName=bucket_name)
        if acl_response.status < 300 and acl_response.body.grants:
            # Check if there is only one grant and it is for the owner with FULL_CONTROL
            if len(acl_response.body.grants) == 1 and acl_response.body.grants[0].permission == 'FULL_CONTROL':
                return True
            return False
        else:
            print("Failed to retrieve bucket ACL.")
            return False
    except Exception as e:
        print(f"Exception occurred while checking if bucket '{bucket_name}' is private: {e}")
        return False

def configure_static_web_hosting(obs_client, bucket_name, index_document, error_document) -> bool:
    try:
        website_configuration = {
            'indexDocument': {'suffix': index_document},
            'errorDocument': {'key': error_document}
        }
        response = obs_client.setBucketWebsite(bucketName=bucket_name, website=website_configuration)
        if response.status < 300:
            print(f"Bucket '{bucket_name}' configured for static web hosting successfully.")
            return True
        else:
            print(f"Error: Unable to configure bucket '{bucket_name}' for static web hosting. Status code: {response.status}")
            return False
    except Exception as e:
        print(f"Exception occurred while configuring bucket '{bucket_name}' for static web hosting: {e}")
        return False

def check_bucket_exists(obs_client, bucket_name) -> bool:
    """
    Check if the bucket already exists.

    Parameters:
    obs_client (ObsClient): The OBS client instance.
    bucket_name (str): The name of the bucket to check.

    Returns:
    bool: True if the bucket exists, False otherwise.
    """
    try:
        obs_client.headBucket(bucketName=bucket_name)
        return True
    except Exception as e:
        if "NoSuchBucket" in str(e):
            return False
        else:
            print(f"Exception occurred while checking bucket existence: {e}")
            return False

def create_bucket(obs_client, bucket_name, region) -> bool:
    """
    Create a new bucket in the OBS account.

    Parameters:
    obs_client (ObsClient): The OBS client instance.
    bucket_name (str): The name of the bucket to create.

    Returns:
    bool: True if the bucket was created successfully, False otherwise.
    """
    try:

        if check_bucket_exists(obs_client, bucket_name):
            raise Exception(f"Bucket '{bucket_name}' already exists. Skipping creation.")

        response = obs_client.createBucket(bucketName=bucket_name, location=region)
        if response.status < 300:
            if not set_bucket_acl_to_private_if_needed(obs_client, bucket_name):
                return False

            res = is_bucket_private(obs_client, bucket_name)
            print (res)
            with open('bucket_policy.json', 'r') as file:
                policy_template = file.read()
                policy_str = policy_template.replace("{bucket_name}", bucket_name)
                print(policy_str)
                obs_client.setBucketPolicy(bucketName=bucket_name, policyJSON=policy_str)

            if not configure_static_web_hosting(obs_client, bucket_name, 'index.html', 'error.html'):
                print("Error configuring bucket as static web hosting", file=sys.stderr)
                return False

                print(f"Error: {e}", file=sys.stderr)
            return True
        else:
            print(f"Error: Unable to create bucket '{bucket_name}'. Status code: {response.status}", file=sys.stderr)
            print('errorCode:', response.errorCode)
            print('errorMessage:', response.errorMessage)
            return False
    except Exception as e:
        print(f"Exception occurred while creating bucket '{bucket_name}': {e}", file=sys.stderr)
        if hasattr(e, 'response'):
            print(f"Response status code: {e.response.status_code}", file=sys.stderr)
            print(f"Response headers: {e.response.headers}", file=sys.stderr)
            print(f"Response body: {e.response.text}", file=sys.stderr)
        return False

def main(bucket_name, access_key_id, secret_access_key, region) -> bool:
    """
    Main function to create a new bucket in the OBS account.

    Parameters:
    bucket_name (str): The name of the bucket to create.
    access_key_id (str): The access key ID for the OBS account.
    secret_access_key (str): The secret access key for the OBS account.
    server (str): The endpoint URL for the OBS service.

    Returns:
    bool: True if the bucket was created successfully, False otherwise.
    """
    obs_client = ObsClient(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        server="https://obs."+region+".myhuaweicloud.com"
    )
    return create_bucket(obs_client, bucket_name, region)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py <bucket_name> <access_key_id> <secret_access_key> <region>")
        sys.exit(1)

    bucket_name, access_key_id, secret_access_key, region = sys.argv[1:]

    result = main(bucket_name, access_key_id, secret_access_key, region)
    print(True if result else False)
    sys.exit(0)