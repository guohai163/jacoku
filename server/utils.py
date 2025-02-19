# -*- coding: utf-8 -*-
import json
from enum import Enum


class CodeProcess(Enum):
    START = 0
    DUMP_JACOCO = 1
    CLONE_CODE = 2
    BUILD_CODE = 3
    GENERATE_REPORT = 4
    OVER = 5
    ERROR = 6


def subprocess_result_2_response(sub_result):
    web_result = {"returnCode": sub_result.returncode, "message": str(sub_result.stdout), "process": ""}
    return json.dumps(web_result)


def gen_response(return_code=0, message="", process=CodeProcess.START):
    web_result = {"returnCode": return_code, "message": message, "process": process}
    return json.dumps(web_result)
