# -*- coding: utf-8 -*-
import io
import os
import shutil
from kubernetes import client, config
import subprocess
from minio import Minio
import time
import uuid



if __name__ == '__main__':
    print('jacoco-report start ...')
    print(os.getenv('MINIO_URL'))