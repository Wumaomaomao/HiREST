import logging, requests
from typing import Any

from hirest.model.request import Request, ContentType

logger = logging.getLogger(__name__)


class Executor:
    """Executor class: execute testcase."""

    def execute(self, request: Request) -> dict[str, Any]:
        """Execute the request and return the response."""
        try:
            logger.info(
                f"Send request — {((str)(request.method)).upper()} {request.rendered_url} : {request.headers} {request.body}"
            )
            response = requests.request(
                method=request.method,
                url=request.rendered_url,
                headers=request.headers,
                json=request.body if request.content_type == ContentType.JSON or request.content_type == ContentType.JSON_UTF8 else None,
                data=(
                    request.body
                    if request.content_type == ContentType.FORM_URLENCODED or request.content_type == ContentType.TEXT
                    else None
                ),
            )
            logger.info(f"Receive response — {response.status_code} {response.text}")
            return {
                "status_code": response.status_code,
                "text": response.text,
                "headers": response.headers,
            }
        except requests.RequestException as e:
            logger.error(
                f"Request {request.method} {request.rendered_url} : {request.headers} {request.body} execute failed: {e}"
            )
