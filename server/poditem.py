# -*- coding: utf-8 -*-


class PodItem:
    """
    pod的实体类
    """

    def __init__(self, pod_name, pod_ns, pod_ip, last_check_time, enable, git_url, git_commit, src_path, html_link):
        self.pod_name = pod_name
        self.pod_ns = pod_ns
        self.pod_ip = pod_ip
        self.last_check_time = last_check_time
        self.enable = enable
        self.git_url = git_url
        self.git_commit = git_commit
        self.src_path = src_path
        self.html_link = html_link

    def __str__(self):
        return 'pod_name: {}, pod_ip: {}, git_commit: {}, git_url: {}\n'.format(self.pod_name, self.pod_ip,
                                                                                self.git_commit, self.git_url)

    def __repr__(self):
        return self.__str__()

    def toJSON(self):
        return {"pod_name": self.pod_name,
                "pod_ns": self.pod_ns,
                "pod_ip": self.pod_ip,
                "last_check_time": self.last_check_time,
                "enable": self.enable,
                "git_url": self.git_url,
                "git_commit": self.git_commit,
                "src_path": self.src_path,
                "html_link": self.html_link}
