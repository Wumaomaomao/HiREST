import logging, random

from typing import Any

from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.model.testcase import TestCase, MutationType
from hirest.model.request import Request, ContentType

from hirest.fuzzer.renderer.resource_pool import ResourcePool

logger = logging.getLogger(__name__)


class Renderer:
    """Renderer class: render the test case to a request."""

    def __init__(
        self,
        base_url: str,
        sample_dynres_prob: float = 0.5,
        bm_mode: bool = False,
        bm_invalid_media_prob: float = 0.1,
        bm_param_location_prob: float = 0.1,
    ):
        """Initialize the renderer with the base url."""
        self.base_url = base_url
        self.dynres_pool = ResourcePool()
        self.sample_dynres_prob = sample_dynres_prob
        self.bm_mode = bm_mode
        self.bm_invalid_media_prob = bm_invalid_media_prob
        self.bm_param_location_prob = bm_param_location_prob

    def render(self, testcase: TestCase, input_space_manager: InputSpaceManager) -> tuple[TestCase, Request]:
        """render the test case to a request.
        Args:
            testcase (TestCase): test case to be rendered.
            input_space_manager (InputSpaceManager): input space manager.
        Returns:
            tuple[TestCase, Request]: test case and request.
        """
        testcase.generate_param_vals(input_space_manager)
        logger.debug(
            f"generate values for the parameters : {testcase.param_vals}"
        )
        self._render_dynres(testcase)

        testcase.generate_request(self.base_url)
        self._apply_bm_request_level_mutations(testcase)
        logger.debug(
            f"generate request for the test case : {testcase.request}"
        )
        return testcase, testcase.request

    def _apply_bm_request_level_mutations(self, testcase: TestCase) -> None:
        """Apply BM-only request-level mutations during rendering."""
        request = testcase.request
        if not request:
            return

        if not self.bm_mode or testcase.mutation_type != MutationType.DESTROY:
            return

        if random.random() < self.bm_invalid_media_prob:
            self._mutate_invalid_media_type(request)

        if random.random() < self.bm_param_location_prob:
            self._mutate_parameter_location(request)

    def _mutate_invalid_media_type(self, request: Request) -> None:
        """Replace JSON content-type with an incompatible media type, keeping body unchanged."""
        current_content_type = request.content_type
        if current_content_type not in (ContentType.JSON, ContentType.JSON_UTF8):
            return

        target_content_type = random.choice([ContentType.TEXT, ContentType.FORM_URLENCODED])
        request.content_type = target_content_type
        request.headers["Content-Type"] = target_content_type
        logger.info(
            "[BM] Invalid Media Type mutation applied: %s -> %s",
            current_content_type,
            target_content_type,
        )

    def _mutate_parameter_location(self, request: Request) -> None:
        """Move one parameter value between query/header/body; path params are excluded."""
        # Candidate sources excluding path params by design.
        source_candidates: list[tuple[str, str, Any]] = []

        for k, v in (request.query_params or {}).items():
            source_candidates.append(("query", k, v))

        for k, v in (request.headers or {}).items():
            if k.lower() == "content-type":
                continue
            source_candidates.append(("header", k, v))

        if isinstance(request.body, dict):
            for k, v in request.body.items():
                source_candidates.append(("body", k, v))

        if not source_candidates:
            return

        source_loc, param_name, param_value = random.choice(source_candidates)
        target_candidates = [loc for loc in ["query", "header", "body"] if loc != source_loc]
        target_loc = random.choice(target_candidates)

        # Remove from source location.
        if source_loc == "query":
            request.query_params.pop(param_name, None)
        elif source_loc == "header":
            request.headers.pop(param_name, None)
        elif source_loc == "body" and isinstance(request.body, dict):
            request.body.pop(param_name, None)

        # Add to target location while preserving name/value.
        if target_loc == "query":
            request.query_params[param_name] = param_value
        elif target_loc == "header":
            request.headers[param_name] = str(param_value)
        elif target_loc == "body":
            if not isinstance(request.body, dict):
                return
            request.body[param_name] = param_value

        # Rebuild URL after potential query mutation.
        request.build_url()
        logger.info(
            "[BM] Parameter Location mutation applied: %s.%s -> %s.%s",
            source_loc,
            param_name,
            target_loc,
            param_name,
        )

    def _render_dynres(self, testcase: TestCase) -> None:
        """render the dynamic resources in the test case.
        Args:
            testcase (TestCase): test case to be rendered.
        """
        for name, value in testcase.param_vals.items():
            short_name = name.split('.')[-1]
            if short_name in self.dynres_pool.pool.keys():
                if random.random() < self.sample_dynres_prob:
                    testcase.param_vals[name] = random.choice(self.dynres_pool.pool[short_name])
                    logger.debug(f'render the param: {name} with dynamic resource value {testcase.param_vals[name]}')


            
