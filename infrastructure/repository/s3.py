from boto3 import client
import os
from config import get_settings

class S3:
    def __init__(self, s3: client, bucket: str) -> None:
        self.s3 = s3
        self.bucket = bucket
    
    def upload(self, car_id, key, data):
        try:
            self.s3.put_object(Bucket= self.bucket, Key=car_id+'/'+key, Body=data)
            return key
        except Exception as e:
            print(e)

    def upload_video(self, video, prefix, key):
        try:
            self.s3.upload_file(Bucket= self.bucket, Key=prefix+'/'+key, Filename=video)
        except Exception as e:
            print(e)
            
    

def make_s3():
    setting = get_settings()
    s3 = client('s3',
                aws_access_key_id = setting.aws_access_key_id,
                aws_secret_access_key=setting.aws_secret_access_key,
    )
    upload = S3(s3=s3, bucket = setting.aws_bucket_name)
    return upload


async def get_S3():
    upload = make_s3
    try:
        yield upload
    finally:
        ...