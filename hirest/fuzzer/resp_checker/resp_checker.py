import logging, json

from typing import Any

from hirest.model.testcase import TestCase
from hirest.model.request import Request
from hirest.model.operation import Operation

logger = logging.getLogger(__name__)


class RespChecker:
    """RespChecker class: process the response and check the status code and content."""

    def __init__(self):
        error_bucket: dict[str, Any]
        self.status_code_bucket: dict[str, dict[str, int | str]] = {}
        content_bucket: dict[str, Any]

    def init_status_code_bucket(self, operations: list[Operation]) -> None:
        """Initialize the status code bucket."""
        self.status_code_bucket["summary"] = {
            "total operation count": len(operations),
            "successful operation count": 0,
            "successful operations": [],
            "failed operations": [],
            "total sended request count": 0,
            "2xx request count": 0,
            "4xx request count": 0,
            "5xx request count": 0,
        }
        for operation in operations:
            self.status_code_bucket[operation.op_name] = {
                "2xx": {
                    "count": 0,
                    "case": list[tuple[Request, str]](),
                },
                "4xx": {
                    "count": 0,
                    "case": list[tuple[Request, str]](),
                },
                "5xx": {
                    "count": 0,
                    "case": list[tuple[Request, str]](),
                },
                "other": {
                    "count": 0,
                    "case": list[tuple[Request, str]](),
                },
            }

    def resp_parse(
        self, testcase: TestCase, request: Request, response: dict[str, Any]
    ) -> None:
        """Parse the response and check the status code and content."""
        self._status_code_check(testcase, response)
        return

    def _status_code_check(self, testcase: TestCase, resp: dict[str, Any]) -> None:
        """Check the status code of the response."""
        status_code = resp["status_code"]
        op_name = testcase.operation.op_name
        status_code_first_digit = str(status_code)[0]

        # update total sended request count and status code request count
        self.status_code_bucket["summary"]["total sended request count"] += 1
        self.status_code_bucket["summary"][f"{status_code_first_digit}xx request count"] += 1

        bucket = self.status_code_bucket[op_name][f"{status_code_first_digit}xx"]

        bucket["count"] += 1
        text = resp["text"]
        if text not in [item[1] for item in bucket["case"]]:
            bucket["case"].append((
                {
                    "rendered_url": testcase.request.rendered_url,
                    "header": testcase.request.headers,
                    "body": testcase.request.body,
                },
                text
            ))
        
    def output_result(self) -> None:
        """Output the results of the response checker."""

        # generate summary of operations results
        for op_name, bucket in self.status_code_bucket.items():
            if op_name == "summary":
                continue
            if bucket["2xx"]["count"] > 0:
                self.status_code_bucket["summary"]["successful operations"].append(op_name)
                self.status_code_bucket["summary"]["successful operation count"] += 1
            elif bucket["4xx"]["count"] > 0 or bucket["5xx"]["count"] > 0:
                self.status_code_bucket["summary"]["failed operations"].append(op_name)
        
        # output the results
        logger.info(json.dumps(self.status_code_bucket, indent=4))
