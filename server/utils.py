# -*- coding: utf-8 -*-


def subprocess_result_2_response(sub_result):
    web_result = {"returnCode": sub_result.returncode, "message": sub_result.stdout}
    return web_result


def gen_response(return_code=0, message=""):
    web_result = {"returnCode": return_code, "message": message}
    return web_result
