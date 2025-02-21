# -*- coding: utf-8 -*-
import json
from enum import Enum


class CodeProcess(str, Enum):
    START = '[START]'
    DUMP_JACOCO = '[DUMP JACOCO]'
    CLONE_CODE = '[CLONE CODE]'
    BUILD_CODE = '[BUILD PROJECT]'
    GENERATE_REPORT = '[GENERATE REPORT]'
    OVER = '[OVER]'
    ERROR = '[ERROR]'


def subprocess_result_2_response(sub_result):
    web_result = {"returnCode": sub_result.returncode, "message": str(sub_result.stdout), "process": ""}
    return json.dumps(web_result)


def gen_response(return_code=0, message="", process=CodeProcess.START):
    web_result = {"returnCode": return_code, "message": message, "process": process}
    return json.dumps(web_result)
