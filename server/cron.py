import getopt
import json
import sys
import os

import log4p
from crontab import CronTab
import asyncio
import tornado.web
import tornado.websocket

import utils
from main import get_pod, generate_jacoco_report

LOG = log4p.GetLogger('__main__').logger

REPORT_PATH = '/data/report/'


def init_cron_task():
    """
    初始化定时任务
    :return:
    """
    cron_manager = CronTab(user=True)
    # 写定时任务,
    jacoco_job = cron_manager.new(
        command='. /etc/environment;python3 /opt/jacoco-data/main.py >> /var/log/jaococ-report.log 2>&1')
    cron_parm = os.getenv('CRON')
    if cron_parm is None:
        jacoco_job.setall('0 1 * * *')
        LOG.info('If the cron parameter is empty, the default time is 1 o\'clock')
    else:
        jacoco_job.setall(cron_parm)
    cron_manager.write()


def env_check():
    mini_enable = os.getenv('MINIO_ENABLE')
    if mini_enable is None:
        return
    else:
        if mini_enable:
            minio_url = os.getenv('MINIO_URL')
            minio_access_key = os.getenv('MINIO_ACCESS')
            minio_secret_key = os.getenv('MINIO_SECRET')
            if minio_url is None or minio_access_key is None or minio_secret_key is None:
                print('The required parameters are empty')
                sys.exit(2)


class ListOfListsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list):
            return obj
        return obj.toJSON()


class AnalysisWebSocket(tornado.websocket.WebSocketHandler):
    waiters = set()

    def check_origin(self, origin):
        return True

    def open(self):
        LOG.info('WS opened')
        AnalysisWebSocket.waiters.add(self)

    def on_message(self, message):
        args = json.loads(message)
        self.write_message(utils.gen_response(0, '接收到请求{},开始分析！！'.format(args['pod_name'])))
        self.write_message(utils.gen_response(0, '', ""))
        generate_jacoco_report(args['pod_name'], args['pod_ip'], args['git_url'], args['git_commit'],
                               args['src_path'], 'html', False, True, self, args['build_path'])
        self.close()

    def on_close(self):
        LOG.info('ws closed')
        AnalysisWebSocket.waiters.remove(self)


# pylint: disable=W0223
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps(get_pod(False), cls=ListOfListsEncoder))


# pylint: disable=W0223
class ReportBrowser(tornado.web.RequestHandler):
    """
    返回报告的静态文件
    """

    def get(self, path):
        LOG.info(path)
        local_path = '{}{}'.format(REPORT_PATH, path)
        if not os.path.exists(local_path):
            raise tornado.web.HTTPError(404)
        if os.path.isdir(local_path):
            if not self.request.path.endswith('/'):
                self.redirect(self.request.path + '/')
                return
        if path[-3:] == 'gif':
            self.set_header("Content-type", "image/gif")
        if path[-3:] == 'css':
            self.set_header("Content-type", "text/css")
        if path[-2:] == 'js':
            self.set_header("Content-type", "text/javascript")

        with open(local_path, 'rb') as f:
            self.write(f.read())
            self.finish()
            return


async def server_start():
    app = tornado.web.Application([
        (r"/api/ws", AnalysisWebSocket),
        (r"/api/list", MainHandler),
        (r"/report/(.*)", ReportBrowser),
    ])
    app.listen(1219)
    await asyncio.Event().wait()


def main():
    """
    主方法
    """
    env_check()
    init_cron_task()
    asyncio.run(server_start())


if __name__ == '__main__':
    main()
