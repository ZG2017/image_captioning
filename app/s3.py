import boto3
from app import config

# upload file to S3 bucket
def upload_to_s3(filepath, bucketname, filename, acl="public-read"):
    s3_client = boto3.client('s3',**config.aws_connection_args)  #
    s3_client.upload_file(filepath, bucketname, filename, ExtraArgs={'ACL':acl})


def create_file(name):
    s3_client = boto3.client('s3',**config.aws_connection_args)
    try:
        response = s3_client.put_object(Bucket =config.S3_BUCKETNAME, Key=name)
    except Exception as e:
        print("create fail")
        return e
