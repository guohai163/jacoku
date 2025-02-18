# -*- coding: utf-8 -*-
import json


def subprocess_result_2_response(sub_result):
    # web_result = '{{"returnCode": "{}", "message": "{}"}}'.format(sub_result.returncode, sub_result.stdout)
    web_result = {"web_result": sub_result.returncode, "message": str(sub_result.stdout)}
    return json.dumps(web_result)


def gen_response(return_code=0, message=""):
    web_result = {"web_result": return_code, "message": message}
    return json.dumps(web_result)
