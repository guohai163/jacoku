# -*- coding: utf-8 -*-
import json


def subprocess_result_2_response(sub_result):
    web_result = {"returnCode": sub_result.returncode, "message": str(sub_result.stdout)}
    return json.dumps(web_result)


def gen_response(return_code=0, message=""):
    web_result = {"returnCode": return_code, "message": message}
    return json.dumps(web_result)
