# -*- coding: utf-8 -*-
import glob
import os
import pickle
import shutil

import log4p
from kubernetes import client, config
import subprocess
from minio import Minio
import time
import re

import utils
from poditem import PodItem

LOG = log4p.GetLogger('__main__').logger

local_base_dir = '/tmp/code_repo/'
DATA_PATH = '/data'
REPORT_PATH = DATA_PATH + '/report/'
check_pickle_file = DATA_PATH + '/last_check.pickle'
report_link_pickle_file = DATA_PATH + '/report_link.pickle'

path_date = time.strftime("%Y-%m-%d", time.localtime())
maven_path = "/opt/maven/bin"

jacoco_cli = "/opt/org.jacoco.cli-0.8.12-nodeps.jar"

git_commit_dic = {}

# pod的最后检查时间
pod_last_check = {}

report_html = {}

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

    # 如果本次和上次commit值想同，不再重新生成字节码文件
    if git_commit_dic.get(project_name) != git_commit:
        result = subprocess.run('git pull && git checkout {}'.format(git_commit), shell=True,
                                cwd=local_base_dir + '/' + project_name,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result


def check_runtime(runtime=False):
    """
    检查运行环境返回结果，影响run输出日志位置
    Args:
        runtime (bool): 运行位置。True，web状态下运行。False 本地运行
    """
    if runtime:
        return subprocess.PIPE
    else:
        return None


def build_java_project(project_name, git_commit, src_path, build_path_switch, runtimes=False):
    """
    通过mvn构建生成
    Args:
        project_name (str): 项目名
    """
    if build_path_switch:
        run_cwd = local_base_dir + '/' + project_name + '/' + src_path
    else:
        run_cwd = local_base_dir + '/' + project_name
    LOG.info('build_path:{}'.format(run_cwd))
    result = subprocess.run(
        'export JAVA_HOME={} && export PATH=$PATH:{} && mvn clean package -Dmaven.test.skip=true'
        .format(jdk_path[11], maven_path), shell=True, cwd=run_cwd,
        stdout=check_runtime(runtimes), stderr=check_runtime(runtimes))
    # 如果pom_path 没传，认为构建了整个项目。下次同commit可以不进行二次构建
    if not build_path_switch:
        git_commit_dic[project_name] = git_commit
    return result


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
            minio_client.fput_object(os.getenv('MINIO_BUCKET'), remote_path, local_file)


def generate_report(jacoco_exec, git_url, git_commit, src_path, project_name, service_name, re_format):
    """
    按指定格式生成报告
    """
    LOG.info("%s\t%s\t%s", jacoco_exec, git_url, git_commit)
    call_command = ''
    result_file = ''
    if re_format == 'xml':
        call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                        'java -jar {} report {} --classfiles ./target/classes '
                        '--sourcefiles ./src/main/java --xml /tmp/{}.xml') \
            .format(jdk_path[11], jdk_path[11], jacoco_cli, jacoco_exec, service_name)
        result_file = '/tmp/{}.xml'.format(service_name)
    else:
        call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                        'java -jar {} report {} --classfiles ./target/classes '
                        '--sourcefiles ./src/main/java --html {}{}/{}') \
            .format(jdk_path[11], jdk_path[11], jacoco_cli, jacoco_exec, REPORT_PATH, project_name, service_name)
        result_file = '{}{}/{}'.format(REPORT_PATH, project_name, service_name)
    LOG.debug(call_command)
    result = subprocess.run(call_command, shell=True, cwd=local_base_dir + '/' + project_name + '/' + src_path,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE
                            )
    return result


def upload_report(project_group, project_name, service_name, re_format):
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
        minio_client.fput_object(os.getenv('MINIO_BUCKET'), destination_file, '/tmp/{}.xml'.format(service_name))
    else:
        destination_path = '{}/{}/{}/{}'.format(path_date, project_group, project_name, service_name)
        upload_local_directory_to_minio('{}{}/{}'.format(REPORT_PATH, project_name, service_name), destination_path
                                        , minio_client)


def check_minio(minio_client):
    """
    检查对象存储桶是否存在
    """
    bucket_name = os.getenv('MINIO_BUCKET')
    found = minio_client.bucket_exists(bucket_name)
    if not found:
        minio_client.make_bucket(bucket_name)
        LOG.info('Created bucket {}'.format(bucket_name))
    else:
        LOG.info('Bucket {} already exists'.format(bucket_name))


def dump_jacoco_data(pod_ip, exec_file):
    """
    dump   数据
    """
    call_command = ('export PATH=$PATH:{}/bin && export JAVA_HOME={} && '
                    'java -jar {} dump --address {} --destfile {}') \
        .format(jdk_path[11], jdk_path[11], jacoco_cli, pod_ip, exec_file)
    result = subprocess.run(call_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result


def generate_jacoco_report(pod_name, pod_ip, git_url, git_commit, src_path, re_format='xml', upload_enable=False,
                           req_web=False, ws_obj=None, build_path_switch=False):
    """
    此方法包括dump数据 ，下载源码产生字节码，生成覆盖率报告.
    Args:
        pod_name (str): pod名字，
        pod_ip (str): pod的IP，jacoco请求时会使用
        git_url (str): git的地址，用来克隆代码使用
        git_commit (str): pod运行时对应的commit版本，用来按commit生成字节码
        src_path (str): 获取字节码的文件的路径，也就是POD对应的目录
        re_format (str): 报告格式，默认为xml。支持html/xml
        upload_enable (bool): 报告是否需要上传报告 默认不需要
        req_web (bool): 运行环境，Flase在本地运行，True WEB下运行。结果值需要返回
        ws_obj (AnalysisWebSocket): web对象，当req_web为True时，需要此参数
        build_path_switch (bool): 构建开关，当为Flase时，build根目录pom。当为True时构建 src_path目录POM
    """
    if src_path is None:
        src_path = ''
    # dump出分析文件
    req_web and path_init()
    exec_file = '/tmp/report_dump/{}.exec'.format(pod_name)
    req_web and ws_obj.write_message(utils.gen_response(0, 'jacoco dump start ...', utils.CodeProcess.DUMP_JACOCO))
    result = dump_jacoco_data(pod_ip, exec_file)
    req_web and ws_obj.write_message(utils.subprocess_result_2_response(result))
    if result is None or result.returncode > 0:
        LOG.error('exec file {} gene fail'.format(exec_file))
        return result
    # 通过正则分解出项目组和项目名
    pattern = re.compile(r'([^/:]+)/([^/.]+)\.git$')
    result = pattern.findall(git_url)
    project_group = result[0][0]
    project_name = result[0][1]
    # 克隆并代码
    req_web and ws_obj.write_message(utils.gen_response(0, '准备克隆项目{}'.format(project_name),
                                                        utils.CodeProcess.CLONE_CODE))
    result = clone_project_local(git_url, project_name, git_commit)
    req_web and ws_obj.write_message(utils.subprocess_result_2_response(result))
    if result is None or result.returncode > 0:
        LOG.error('project clone {} fail commit {}'.format(project_name, git_commit))
        return result
    # build项目
    req_web and ws_obj.write_message(utils.gen_response(0, '准备构建项目{}'.format(project_name),
                                                        utils.CodeProcess.BUILD_CODE))
    result = build_java_project(project_name, git_commit, src_path, build_path_switch, req_web)
    req_web and ws_obj.write_message(utils.subprocess_result_2_response(result))
    if result is None or result.returncode > 0:
        LOG.error('project build {} fail commit {}'.format(project_name, git_commit))
        return result
    # 生成 报告
    service_name = re.compile(r'(.+)-[\d\w]+-[\d\w]+$').findall(pod_name)[0]
    if os.path.exists(local_base_dir + '/' + project_name + '/' + src_path):
        req_web and ws_obj.write_message(utils.gen_response(0, '生成报告{}'.format(pod_name),
                                                            utils.CodeProcess.GENERATE_REPORT))
        generate_result = generate_report(exec_file, git_url, git_commit, src_path, project_name, service_name,
                                          re_format)
        req_web and ws_obj.write_message(utils.subprocess_result_2_response(generate_result))
        if upload_enable and generate_result.returncode <= 0:
            upload_report(project_group, project_name, service_name, re_format)
        pod_last_check[pod_name] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if re_format == 'html' and generate_result:
            report_html[service_name] = '/report/{}/{}/index.html'.format(project_name, service_name)
        if req_web:
            with open(check_pickle_file, 'wb') as check_time_file:
                pickle.dump(pod_last_check, check_time_file)
            with open(report_link_pickle_file, 'wb') as re_link_file:
                pickle.dump(report_html, re_link_file)
        req_web and ws_obj.write_message(utils.gen_response(0, '🎉🎉💯项目{}分析成功🌷🎉🎉'.format(service_name),
                                                            utils.CodeProcess.OVER))
        return '生成成功'
    else:
        req_web and ws_obj.write_message(
            utils.gen_response(1, '项目{}路径配置错误'.format(pod_name), utils.CodeProcess.ERROR))
        LOG.error('项目{}路径配置错误'.format(pod_name))
        return '项目{}路径配置错误'.format(pod_name)


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
                build_path_switch = False
                if 'jacoco/build-path-switch' in i.metadata.annotations:
                    build_path_switch = i.metadata.annotations.get('jacoco/build-path-switch')
                pod_item = PodItem(i.metadata.name, i.metadata.namespace, i.status.pod_ip, last_time,
                                   i.metadata.annotations.get('jacoco/enable').lower() == 'true',
                                   i.metadata.annotations.get('jacoco/git-url'),
                                   i.metadata.annotations.get('jacoco/git-commit'),
                                   i.metadata.annotations.get('jacoco/src-path'),
                                   html_link, build_path_switch)
                pod_list.append(pod_item)
                LOG.info('{}\t{}\t{}'.format(i.status.pod_ip, i.metadata.namespace, i.metadata.name))
            else:
                pod_item = PodItem(i.metadata.name, i.metadata.namespace, i.status.pod_ip, None,
                                   False, '', '', '', '', False)
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
                               upload_mini_enable, False, build_path_switch=pod.build_path_switch)
    # 多进程中共享文件使用
    with open(check_pickle_file, 'wb') as check_file:
        pickle.dump(pod_last_check, check_file)

    with open(report_link_pickle_file, 'wb') as link_file:
        pickle.dump(report_html, link_file)
