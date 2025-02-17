# -*- coding: utf-8 -*-
import glob
import io
import os
import pickle
import shutil

import log4p
from kubernetes import client, config
import subprocess
from minio import Minio
import time
import uuid
import re

from poditem import PodItem

LOG = log4p.GetLogger('__main__').logger

bucket_name = "jacoco-report"
local_base_dir = '/tmp/code_repo/'
REPORT_PATH = '/data/report/'

path_date = time.strftime("%Y-%m-%d", time.localtime())
maven_path = "/opt/maven/bin"

jacoco_cli = "/opt/org.jacoco.cli-0.8.12-nodeps.jar"

git_commit_dic = {}

# pod的最后检查时间
pod_last_check = {}

check_pickle_file = "last_check.pickle"

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
    if not os.path.exists(REPORT_PATH):
        os.makedirs(REPORT_PATH)


def clone_project_local(git_url, project_name, git_commit):
    """
    克隆代码
    """
    if not os.path.exists('{}{}'.format(local_base_dir, project_name)):
        subprocess.call('git clone {}'.format(git_url), shell=True, cwd=local_base_dir)  ##-b develop
        git_commit_dic[project_name] = ''
    if git_commit_dic.get(project_name) != git_commit:
        subprocess.call('git checkout {}'.format(git_commit), shell=True, cwd=local_base_dir + '/' + project_name)
        subprocess.call('export JAVA_HOME={} && export PATH=$PATH:{} && mvn clean package -Dmaven.test.skip=true'
                        .format(jdk_path[11], maven_path), shell=True, cwd=local_base_dir + '/' + project_name)
        git_commit_dic[project_name] = git_commit


def upload_local_directory_to_minio(local_path, minio_path, minio_client):
    """
    如果生成报告为html格式，上传目录

    Parameters:
        local_path - 本地文件路径
        minio_path - 远程文件路径
    """
    assert os.path.isdir(local_path)
    for local_file in glob.glob(local_path + '/**'):
        local_file = local_file.replace(os.sep, "/")
        if not os.path.isfile(local_file):
            upload_local_directory_to_minio(
                local_file, minio_path + "/" + os.path.basename(local_file), minio_client)
        else:
            remote_path = os.path.join(
                minio_path, local_file[1 + len(local_path):])
            remote_path = remote_path.replace(
                os.sep, "/")
            minio_client.fput_object(bucket_name, remote_path, local_file)


def generate_report(jacoco_exec, git_url, git_commit, src_path, project_name, report_format):
    """
    按指定格式生成报告
    """
    LOG.info("%s\t%s\t%s", jacoco_exec, git_url, git_commit)
    call_command = ''
    if report_format == 'xml':
        call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                        'java -jar {} report /tmp/report.exec --classfiles ./target/classes '
                        '--sourcefiles ./src/main/java --xml /tmp/report.xml') \
            .format(jdk_path[11], jdk_path[11], jacoco_cli)
    else:
        call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                        'java -jar {} report /tmp/report.exec --classfiles ./target/classes '
                        '--sourcefiles ./src/main/java --html /tmp/report_html') \
            .format(jdk_path[11], jdk_path[11], jacoco_cli)
    print(call_command)
    subprocess.call(call_command, shell=True, cwd=local_base_dir + '/' + project_name + '/' + src_path)


def upload_report(project_group, project_name, pod_name, report_format):
    """
    上传报告到minio对象存储
    """
    minio_client = Minio(os.getenv('MINIO_URL'),
                         access_key=os.getenv('MINIO_ACCESS'),
                         secret_key=os.getenv('MINIO_SECRET'),
                         )
    check_minio(minio_client)
    if report_format == 'xml':
        destination_file = '{}/{}/{}/{}.xml'.format(path_date, project_group, project_name, pod_name)
        minio_client.fput_object(bucket_name, destination_file, '/tmp/report.xml')
    else:
        destination_path = '{}/{}/{}/{}'.format(path_date, project_group, project_name, pod_name)
        upload_local_directory_to_minio('/tmp/report_html', destination_path, minio_client)


def clean_report():
    subprocess.call('rm -rf /tmp/report.xml /tmp/report.exec', shell=True)


def check_minio(minio_client):
    found = minio_client.bucket_exists(bucket_name)
    if not found:
        minio_client.make_bucket(bucket_name)
        print("Created bucket", bucket_name)
    else:
        print("Bucket", bucket_name, "already exists")


def generate_jacoco_report(pod_name, pod_ip, git_url, git_commit, src_path, report_format, upload_mini_enable):
    """
    此方法包括dump数据 ，下载源码产生字节码，生成覆盖率报告
    """
    call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                    'java -jar {} dump --address {} --destfile /tmp/report.exec').format(jdk_path[11], jdk_path[11],
                                                                                         jacoco_cli,
                                                                                         pod_ip)
    subprocess.call(call_command, shell=True)
    # 通过正则分解出项目组和项目名
    pattern = re.compile(r'([^/:]+)/([^/.]+)\.git$')
    result = pattern.findall(git_url)
    project_group = result[0][0]
    project_name = result[0][1]
    clone_project_local(git_url, project_name, git_commit)
    generate_report('/tmp/{}.exec'.format(pod_ip), git_url, git_commit, src_path, project_name, report_format)
    upload_report(project_group, project_name, pod_name, report_format)
    pod_last_check[pod_name] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    clean_report()


def get_pod(is_jacoco_enable):
    """
    遍历集群内所有POD找到有jacoco/enabel=true的POD进行jacoco生成
    """
    config.load_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    pod_list = []
    pod_last_check_temp = {}
    if os.path.exists(check_pickle_file):
        with open(check_pickle_file, 'rb') as check_file_r:
            pod_last_check_temp = pickle.load(check_file_r)
    for i in ret.items:
        if i.metadata.annotations is not None:
            if i.metadata.annotations.get('jacoco/enable') is not None:
                last_time = None
                if not pod_last_check_temp.get(i.metadata.name) is None:
                    last_time = pod_last_check_temp[i.metadata.name]
                pod_item = PodItem(i.metadata.name, i.metadata.namespace, i.status.pod_ip, last_time,
                                   i.metadata.annotations.get('jacoco/enable').lower() == 'true',
                                   i.metadata.annotations.get('jacoco/git-url'),
                                   i.metadata.annotations.get('jacoco/git-commit'),
                                   i.metadata.annotations.get('jacoco/src-path'))
                pod_list.append(pod_item)
                print("%s\t%s\t%s\t" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
            else:
                pod_item = PodItem(i.metadata.name, i.metadata.namespace, i.status.pod_ip, None,
                                   False, '', '', '')
                if not is_jacoco_enable:
                    pod_list.append(pod_item)
    return pod_list


def get_minio_enable():
    mini_enable = os.getenv('MINIO_ENABLE')
    if mini_enable is None:
        return False
    else:
        return mini_enable


def get_report_format():
    """
    通过环境变量确认文件格式
    """
    format_parm = os.getenv('FORMAT')
    if format_parm is None:
        return 'html'
    else:
        return format_parm


if __name__ == '__main__':
    print('jacoku start ...')
    path_init()
    # 获取报告格式
    report_format = get_report_format()
    # 获取是否上传
    upload_mini_enable = get_minio_enable()
    list_pod = get_pod(True)
    for pod in list_pod:
        generate_jacoco_report(pod.pod_name, pod.pod_ip, pod.git_url, pod.git_commit, pod.src_path, report_format,
                               upload_mini_enable)
    # 多进程中共享文件使用
    with open(check_pickle_file, 'wb') as check_file:
        pickle.dump(pod_last_check, check_file)
