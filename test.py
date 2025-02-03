# -*- coding: utf-8 -*-
import io
import os
import shutil
import asyncio
import tornado
import json
from kubernetes import client, config

from server.poditem import PodItem


def get_pod(is_jacoco_enable):
    """
    遍历集群内所有POD找到有jacoco/enabel=true的POD进行jacoco生成
    TODO: 此方法需要重构，返回一个集合体
    """
    config.load_config()
    v1 = client.CoreV1Api()
    ret = v1.list_pod_for_all_namespaces(watch=False)
    pod_list = []
    for i in ret.items:
        if i.metadata.annotations is not None:
            if i.metadata.annotations.get('jacoco/enable') is not None:
                pod_item = PodItem(i.metadata.name, i.metadata.namespace, i.status.pod_ip, None,
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


class ListOfListsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list):
            return obj
        return obj.toJSON()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps(get_pod(), cls=ListOfListsEncoder))


async def server_start():
    app = tornado.web.Application([
        (r"/", MainHandler),
    ])
    app.listen(8888)
    await asyncio.Event().wait()


if __name__ == '__main__':
    print('jacoco-report start ...')
    asyncio.run(server_start())
