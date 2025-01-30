# -*- coding: utf-8 -*-
import io
import os
import shutil
from kubernetes import client, config
import subprocess
from minio import Minio
import time
import uuid

minio_client = Minio(os.getenv('MINIO_URL'),
                     access_key=os.getenv('MINIO_ACCESS'),
                     secret_key=os.getenv('MINIO_SECRET'),
                     )

bucket_name = "jacoco-report"
local_base_dir = '/tmp/code_repo/'

path_date = time.strftime("%Y-%m-%d", time.localtime())
maven_path = "/opt/apache-maven-3.9.9/bin"

jacoco_cli = "/opt/org.jacoco.cli-0.8.12-nodeps.jar"

git_commit_dic = {}

def check_minio():
    found = minio_client.bucket_exists(bucket_name)
    if not found:
        minio_client.make_bucket(bucket_name)
        print("Created bucket", bucket_name)
    else:
        print("Bucket", bucket_name, "already exists")

if __name__ == '__main__':
    print('jacoco-report start ...')
    check_minio()