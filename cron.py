import getopt
import sys
import os 
import time
import log4p
from crontab import CronTab

LOG = log4p.GetLogger('__main__').logger


def init_cron_task():
    """
    初始化定时任务
    :return:
    """
    cron_manager = CronTab(user=True)
    # 写定时任务,
    jacoco_job = cron_manager.new(
        command='. /etc/environment;python3 /opt/jacoco-data/main.py >> /var/log/git_backup.log 2>&1')
    cron_parm = os.getenv('CRON')
    if cron_parm is None:
        jacoco_job.setall('0 1 * * *')
        LOG.info('If the cron parameter is empty, the default time is 1 o\'clock')
    else:
        jacoco_job.setall(cron_parm)
    cron_manager.write()

def env_check():
    minio_url = os.getenv('MINIO_URL')
    minio_access_key = os.getenv('MINIO_ACCESS')
    minio_secret_key = os.getenv('MINIO_SECRET')
    if minio_url is None or minio_access_key is None or minio_secret_key is None:
        print('The required parameters are empty')
        sys.exit(2)


def main():
    init_cron_task()
    while True:
        time.sleep(60)
        LOG.info('sleep 60s')


if __name__ == '__main__':
    env_check()
    main()
