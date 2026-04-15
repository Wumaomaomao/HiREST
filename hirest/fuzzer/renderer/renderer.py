import logging, random

from typing import Any

from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.model.testcase import TestCase
from hirest.model.request import Request

from hirest.fuzzer.renderer.resource_pool import ResourcePool

logger = logging.getLogger(__name__)


class Renderer:
    """Renderer class: render the test case to a request."""

    def __init__(self, base_url: str, sample_dynres_prob: float = 0.5):
        """Initialize the renderer with the base url."""
        self.base_url = base_url
        self.dynres_pool = ResourcePool()
        self.sample_dynres_prob = sample_dynres_prob

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
        logger.debug(
            f"generate request for the test case : {testcase.request}"
        )
        return testcase, testcase.request

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


            
