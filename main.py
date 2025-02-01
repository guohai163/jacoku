# -*- coding: utf-8 -*-
import io
import os
import shutil
from kubernetes import client, config
import subprocess
from minio import Minio
import time
import uuid
import re

minio_client = Minio(os.getenv('MINIO_URL'),
                     access_key=os.getenv('MINIO_ACCESS'),
                     secret_key=os.getenv('MINIO_SECRET'),
                     )

bucket_name = "jacoco-report"
local_base_dir = '/tmp/code_repo/'

path_date = time.strftime("%Y-%m-%d", time.localtime())
maven_path = "/opt/maven/bin"

jacoco_cli = "/opt/org.jacoco.cli-0.8.12-nodeps.jar"

git_commit_dic = {}

jdk_path = {11: "/opt/jdk11",
            17: "/opt/jdk17",
            21: "/opt/jdk21"}


def path_init():
    """
    目录初始
    :return:
    """
    if os.path.exists(local_base_dir):
        shutil.rmtree(local_base_dir)
    os.makedirs(local_base_dir)


def clone_project_local(git_url, project_name, git_commit):
    """
    克隆代码
    """
    if not os.path.exists('{}{}'.format(local_base_dir, project_name)):
        subprocess.call('git clone {}'.format(git_url), shell=True, cwd=local_base_dir)  ##-b develop
        git_commit_dic[project_name] = ''
    if git_commit_dic.get(project_name) != git_commit:
        subprocess.call('git checkout {}'.format(git_commit), shell=True, cwd=local_base_dir + '/' + project_name)
        subprocess.call('export JAVA_HOME={} && export PATH=$PATH:{} && mvn package'.format(jdk_path[11], maven_path),
                        shell=True, cwd=local_base_dir + '/' + project_name)
        git_commit_dic[project_name] = git_commit


def generate_report(jacoco_exec, git_url, git_commit, src_path, project_name):
    print("%s\t%s\t%s" % (jacoco_exec, git_url, git_commit))
    call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                    'java -jar {} report /tmp/report.exec --classfiles ./target/classes  --sourcefiles ./src/main/java '
                    '--xml /tmp/report.xml').format(jdk_path[11], jdk_path[11], jacoco_cli)
    print(call_command)
    subprocess.call(call_command, shell=True, cwd=local_base_dir + '/' + project_name + '/' + src_path)


def upload_report(project_group, project_name):
    destination_file = '{}/{}::{}/{}.xml'.format(path_date, project_group, project_name, uuid.uuid1())
    minio_client.fput_object(bucket_name, destination_file, '/tmp/report.xml')


def clean_report():
    subprocess.call('rm -rf /tmp/report.xml /tmp/report.exec', shell=True)


def check_minio():
    found = minio_client.bucket_exists(bucket_name)
    if not found:
        minio_client.make_bucket(bucket_name)
        print("Created bucket", bucket_name)
    else:
        print("Bucket", bucket_name, "already exists")


def generate_jacoco_report(pod_ip, git_url, git_commit, src_path):
    """
    此方法包括dump数据 ，下载源码产生字节码，生成覆盖率报告
    """
    call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                    'java -jar {} dump --address {} --destfile /tmp/report.exec').format(jdk_path[11], jdk_path[11],
                                                                                         jacoco_cli,
                                                                                         pod_ip)
    subprocess.call(call_command, shell=True)
    # 通过正则分解出项目组和项目名
    pattern = re.compile('([^/:]+)/([^/.]+)\.git$')
    result = pattern.findall(git_url)
    project_group = result[0][0]
    project_name = result[0][1]
    clone_project_local(git_url, project_name, git_commit)
    generate_report('/tmp/{}.exec'.format(pod_ip), git_url, git_commit, src_path, project_name)
    upload_report(project_group, project_name)
    clean_report()


def get_pod():
    """
    遍历集群内所有POD找到有jacoco/enabel=true的POD进行jacoco生成
    TODO: 此方法需要重构，返回一个集合体
    """
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        if i.metadata.annotations is not None:
            if i.metadata.annotations.get('jacoco/enable') is not None:
                print("%s\t%s\t%s\t" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
                generate_jacoco_report(i.status.pod_ip, i.metadata.annotations.get('jacoco/git-url'),
                                       i.metadata.annotations.get('jacoco/git-commit'),
                                       i.metadata.annotations.get('jacoco/src-path'))


if __name__ == '__main__':
    print('jacoco-report start ...')
    check_minio()
    path_init()
    get_pod()
