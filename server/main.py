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

report_html = {}

check_pickle_file = "last_check.pickle"
report_link_pickle_file = "report_link.pickle"

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
    if os.path.exists('/tmp/report_dump/'):
        shutil.rmtree('/tmp/report_dump/')
    os.makedirs('/tmp/report_dump/')
    if not os.path.exists(REPORT_PATH):
        os.makedirs(REPORT_PATH)


def clone_project_local(git_url, project_name, git_commit):
    """
    克隆代码,并对项目进行编译。生成字节码
    """
    if not os.path.exists('{}{}'.format(local_base_dir, project_name)):
        subprocess.call('git clone {}'.format(git_url), shell=True, cwd=local_base_dir)
        git_commit_dic[project_name] = ''
    if git_commit_dic.get(project_name) != git_commit:
        subprocess.call('git pull && git checkout {}'.format(git_commit), shell=True,
                        cwd=local_base_dir + '/' + project_name)
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


def generate_report(jacoco_exec, git_url, git_commit, src_path, project_name, service_name, re_format):
    """
    按指定格式生成报告
    """
    LOG.info("%s\t%s\t%s", jacoco_exec, git_url, git_commit)
    call_command = ''
    if re_format == 'xml':
        call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                        'java -jar {} report {} --classfiles ./target/classes '
                        '--sourcefiles ./src/main/java --xml /tmp/{}.xml') \
            .format(jdk_path[11], jdk_path[11], jacoco_cli, jacoco_exec, service_name)
    else:
        call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                        'java -jar {} report {} --classfiles ./target/classes '
                        '--sourcefiles ./src/main/java --html {}{}/{}') \
            .format(jdk_path[11], jdk_path[11], jacoco_cli, jacoco_exec, REPORT_PATH, project_name, service_name)
    print(call_command)
    subprocess.call(call_command, shell=True, cwd=local_base_dir + '/' + project_name + '/' + src_path)


def upload_report(project_group, project_name, pod_name, service_name, re_format):
    """
    上传报告到minio对象存储
    """
    minio_client = Minio(os.getenv('MINIO_URL'),
                         access_key=os.getenv('MINIO_ACCESS'),
                         secret_key=os.getenv('MINIO_SECRET'),
                         )
    check_minio(minio_client)
    if re_format == 'xml':
        destination_file = '{}/{}/{}/{}.xml'.format(path_date, project_group, project_name, service_name)
        minio_client.fput_object(bucket_name, destination_file, '/tmp/{}.xml'.format(service_name))
    else:
        destination_path = '{}/{}/{}/{}'.format(path_date, project_group, project_name, service_name)
        upload_local_directory_to_minio('{}{}/{}'.format(REPORT_PATH, project_name, service_name), destination_path
                                        , minio_client)


def check_minio(minio_client):
    found = minio_client.bucket_exists(bucket_name)
    if not found:
        minio_client.make_bucket(bucket_name)
        print("Created bucket", bucket_name)
    else:
        print("Bucket", bucket_name, "already exists")


def generate_jacoco_report(pod_name, pod_ip, git_url, git_commit, src_path, re_format, upload_enable):
    """
    此方法包括dump数据 ，下载源码产生字节码，生成覆盖率报告
    """
    # dump出分析文件
    exec_file = '/tmp/report_dump/{}.exec'.format(pod_name)
    call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                    'java -jar {} dump --address {} --destfile {}') \
        .format(jdk_path[11], jdk_path[11], jacoco_cli, pod_ip, exec_file)
    subprocess.call(call_command, shell=True)
    if not os.path.exists(exec_file):
        LOG.error('exec file {} gene fail', exec_file)
        return 'exec gen fail!'
    # 通过正则分解出项目组和项目名
    pattern = re.compile(r'([^/:]+)/([^/.]+)\.git$')
    result = pattern.findall(git_url)
    project_group = result[0][0]
    project_name = result[0][1]
    # 克隆并构建代码
    clone_project_local(git_url, project_name, git_commit)
    # 生成 报告
    service_name = re.compile(r'(.+)-[\d\w]+-[\d\w]+$').findall(pod_name)[0]
    if os.path.exists(local_base_dir + '/' + project_name + '/' + src_path):
        generate_report(exec_file, git_url, git_commit, src_path, project_name, service_name, re_format)
        if upload_enable:
            upload_report(project_group, project_name, pod_name, service_name, re_format)
        pod_last_check[pod_name] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if re_format == 'html':
            report_html[pod_name] = '/report/{}/{}'.format(project_name, service_name)
    else:
        LOG.error('项目{}路径配置错误'.format(pod_name))


def get_pod(is_jacoco_enable):
    """
    遍历集群内所有POD找到有jacoco/enabel=true的POD进行jacoco生成
    """
    config.load_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    pod_list = []
    pod_last_check_temp = {}
    report_html_link = {}
    if os.path.exists(check_pickle_file):
        with open(check_pickle_file, 'rb') as check_file_r:
            pod_last_check_temp = pickle.load(check_file_r)
    if os.path.exists(report_link_pickle_file):
        with open(report_link_pickle_file, 'rb') as html_link_r:
            report_html_link = pickle.load(html_link_r)
    for i in ret.items:
        if i.metadata.annotations is not None:
            if i.metadata.annotations.get('jacoco/enable') is not None:
                last_time = None
                if not pod_last_check_temp.get(i.metadata.name) is None:
                    last_time = pod_last_check_temp[i.metadata.name]
                html_link = None
                if not report_html_link.get(re.compile(r'(.+)-[\d\w]+-[\d\w]+$').findall(i.metadata.name)[0]) is None:
                    html_link = report_html_link[re.compile(r'(.+)-[\d\w]+-[\d\w]+$').findall(i.metadata.name)[0]]
                pod_item = PodItem(i.metadata.name, i.metadata.namespace, i.status.pod_ip, last_time,
                                   i.metadata.annotations.get('jacoco/enable').lower() == 'true',
                                   i.metadata.annotations.get('jacoco/git-url'),
                                   i.metadata.annotations.get('jacoco/git-commit'),
                                   i.metadata.annotations.get('jacoco/src-path'),
                                   html_link)
                pod_list.append(pod_item)
                print("%s\t%s\t%s\t" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
            else:
                pod_item = PodItem(i.metadata.name, i.metadata.namespace, i.status.pod_ip, None,
                                   False, '', '', '', '')
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

    with open(report_link_pickle_file, 'wb') as link_file:
        pickle.dump(report_html, link_file)
