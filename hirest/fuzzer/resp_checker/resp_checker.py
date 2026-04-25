import logging, json
from pathlib import Path

from typing import Any, Optional

from hirest.model.testcase import TestCase
from hirest.model.request import Request
from hirest.model.operation import Operation

logger = logging.getLogger(__name__)


class RespChecker:
    """RespChecker class: process the response and check the status code and content."""

    def __init__(
        self,
        summary_only: bool = False,
        bugs_mode: bool = False,
        bugs_filepath: Optional[str] = None,
    ):
        error_bucket: dict[str, Any]
        self.status_code_bucket: dict[str, dict[str, int | str]] = {}
        content_bucket: dict[str, Any]
        self.summary_only = summary_only
        self.bugs_mode = bugs_mode
        self.bugs_filepath = Path(bugs_filepath) if (bugs_mode and bugs_filepath) else None
        if self.bugs_filepath is not None:
            self.bugs_filepath.parent.mkdir(parents=True, exist_ok=True)
            if not self.bugs_filepath.exists():
                self.bugs_filepath.write_text("[]\n", encoding="utf-8")

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
        self._status_code_check(testcase, request, response)
        return

    def _status_code_check(self, testcase: TestCase, request: Request, resp: dict[str, Any]) -> None:
        """Check the status code of the response."""
        status_code = resp["status_code"]
        op_name = testcase.operation.op_name
        status_code_first_digit = str(status_code)[0]
        status_key = f"{status_code_first_digit}xx" if status_code_first_digit in {"2", "4", "5"} else "other"

        # update total sended request count and status code request count
        self.status_code_bucket["summary"]["total sended request count"] += 1
        if status_key != "other":
            self.status_code_bucket["summary"][f"{status_code_first_digit}xx request count"] += 1

        bucket = self.status_code_bucket[op_name][status_key]

        bucket["count"] += 1

        if self.bugs_mode and 500 <= status_code < 600:
            self._append_bug_case(request=request, resp=resp)

        if self.summary_only:
            return

        text = resp["text"]
        if text not in [item[1] for item in bucket["case"]]:
            bucket["case"].append((
                {
                    "rendered_url": request.rendered_url,
                    "header": request.headers,
                    "body": request.body,
                },
                text
            ))

    def _append_bug_case(self, request: Request, resp: dict[str, Any]) -> None:
        if self.bugs_filepath is None:
            return

        bug_item = [
            {
                "rendered_url": request.rendered_url,
                "header": request.headers,
                "body": request.body,
            },
            {
                "status_code": resp.get("status_code"),
                "text": resp.get("text", ""),
                "headers": dict(resp.get("headers", {})),
            },
        ]

        # Append to the JSON array in-place to avoid rewriting the whole file on every 5xx.
        item_json = json.dumps(bug_item, ensure_ascii=False)
        path = self.bugs_filepath

        with path.open("rb+") as f:
            f.seek(0, 2)
            size = f.tell()

            if size == 0:
                f.write(b"[]\n")
                f.seek(0, 2)
                size = f.tell()

            pos = size - 1
            last_non_ws = None
            while pos >= 0:
                f.seek(pos)
                ch = f.read(1)
                if ch not in b" \t\r\n":
                    last_non_ws = (pos, ch)
                    break
                pos -= 1

            if last_non_ws is None:
                f.seek(0)
                f.write(("[\n" + item_json + "\n]\n").encode("utf-8"))
                f.truncate()
                return

            end_pos, end_ch = last_non_ws
            if end_ch != b"]":
                # Recover from malformed content by resetting to a fresh array.
                f.seek(0)
                f.write(("[\n" + item_json + "\n]\n").encode("utf-8"))
                f.truncate()
                return

            prev_pos = end_pos - 1
            prev_non_ws_ch = None
            while prev_pos >= 0:
                f.seek(prev_pos)
                ch = f.read(1)
                if ch not in b" \t\r\n":
                    prev_non_ws_ch = ch
                    break
                prev_pos -= 1

            is_empty_array = prev_non_ws_ch == b"["
            f.seek(end_pos)
            if is_empty_array:
                f.write(("\n" + item_json + "\n]\n").encode("utf-8"))
            else:
                f.write((",\n" + item_json + "\n]\n").encode("utf-8"))
            f.truncate()
        
    def output_result(self) -> dict[str, Any]:
        """Output the results of the response checker and return summary."""

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
        if self.summary_only:
            logger.info(json.dumps(self.status_code_bucket["summary"], indent=4))
            return self.status_code_bucket["summary"]

        logger.info(json.dumps(self.status_code_bucket, indent=4))
        return self.status_code_bucket["summary"]
