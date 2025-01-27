import getopt
import sys

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
    mail_job = cron_manager.new(
        command='. /etc/environment;python3 /opt/jacoco-data/main.py >> /var/log/git_backup.log 2>&1')
    mail_job.setall('0 1 * * *')
    cron_manager.write()


def main():
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'hlt:', ['back', 'init'])
    except getopt.GetoptError as err:
        LOG.error(str(err))
        sys.exit(2)
    for o, a in optlist:
        if o in ('-i', '--init'):
            init_cron_task()
            while True:
                time.sleep(60)
                LOG.info('sleep 60s')


if __name__ == '__main__':
    main()
