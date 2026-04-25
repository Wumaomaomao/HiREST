import logging
import time
import json
from typing import Callable, Optional

from tqdm import tqdm

from hirest.model.operation import Operation
from hirest.model.testcase import TestCase, TestCasePool

from hirest.model.request import Request

from hirest.fuzzer.mutator.controller.controller import MutationController
from hirest.fuzzer.renderer.renderer import Renderer
from hirest.fuzzer.executor.executor import Executor
from hirest.fuzzer.resp_checker.resp_checker import RespChecker

from hirest.fuzzer.case_manager import CaseManager
from hirest.fuzzer.input_space_manager import InputSpaceManager


logger = logging.getLogger(__name__)


class Fuzzer:
    """fuzzer class: responsible for managing the cosrest fuzzing process of online phase.
    fuzzing process is a loop that continuously mutates the test cases and sends requests to the target API, including:

        1. init: initialize the fuzzer with the operation and the test case pool.
        2. select: select the operation and the test case pool.
        3. mutate: mutate the selected test case.
        4. render: generate the request template and render the parameters of the request.
        5. execute: send the request to the target API and receive the response.
        6. response checker: analyze the response and update the test case pool.

    """

    def __init__(
        self,
        input_space_manager: InputSpaceManager,
        case_manager: CaseManager,
        mutation_controller: MutationController,
        renderer: Renderer,
        executor: Executor,
        response_checker: RespChecker,
        max_requests=100,
        time_limit=60,
        on_request_sent: Optional[Callable[[int], None]] = None,
    ):
        """initialize the basic configuration of the fuzzer.
        Args:
            max_requests (int): max requests to be sent.
            time_limit (int): time limit of the fuzzing process.
            max_sequence_length (int): max sequence length of the test case.
        """

        self.max_requests = max_requests
        self.time_limit = time_limit

        """initialize the main components of the fuzzer."""
        self.mutation_controller = mutation_controller
        self.renderer = renderer
        self.executor = executor
        self.response_checker = response_checker

        """initialize the main managers of the fuzzer."""
        self.input_space_manager = input_space_manager
        self.case_manager = case_manager

        self.response_checker.init_status_code_bucket(
            operations=list(self.case_manager.operations.values())
        )

        self.send_requests = 0
        self.on_request_sent = on_request_sent

    def start(self):
        """start the fuzzing process util the max requests or time limit is reached."""
        start_time = time.time()

        logger.info(
            f"cosrest Fuzzer started: max_requests={self.max_requests}, time_limit={self.time_limit}"
        )

        with tqdm(total=self.max_requests, desc="Fuzzing requests", unit=" request") as pbar:
            while self.send_requests < self.max_requests:
                elasped_time = time.time() - start_time
                if elasped_time >= self.time_limit:
                    break
                try:
                    self.exec_loop_iteration()
                    self.send_requests += 1
                    if self.on_request_sent:
                        self.on_request_sent(self.send_requests)
                    pbar.update(1)
                except Exception as e:
                    logger.error(
                        f"Error raised during the fuzzing process: {e}", exc_info=True
                    )                    
                    continue

        logger.info(
            f"cosrest Fuzzer finished: send_requests={self.send_requests}, time_limit={self.time_limit}"
        )

        self.response_checker.output_result()

    def exec_loop_iteration(self):
        """execute the loop iteration of the fuzzing process."""
        testcase, isMutated = self.case_manager.next_testcase()

        if isMutated:
            # [**] ablation hierarchical mutation
            # """if the testcase is extended, we need to mutate and render a new testcase."""
            testcase = self.mutation_controller.mutate(testcase)
            logger.info(f"Mutated testcase: {testcase}")

            testcase, request = self.renderer.render(testcase, self.input_space_manager)
            logger.info(f"Rendered request: {request}")
            testcase.request = request

        request = testcase.request
        if request is None:
            logger.error(
                f"Request is None for testcase: {testcase.operation.op_name}, skipping..."
            )
            return

        response = self.executor.execute(request)
        logger.info(f"Received response: {response['status_code']}, {response['text']}")

        self.handle_execution(testcase, request, response)

    def handle_execution(
        self, testcase: TestCase, request: Request, response: dict[str, str]
    ):
        """handle the execution of the testcase, including parsing the response and updating the test case pool."""
        self.response_checker.resp_parse(
            testcase=testcase, request=request, response=response
        )
        self.case_manager.handle_execution(
            testcase=testcase,
            response=response,
        )
        
        self.renderer.dynres_pool.extract_dynres(request=request,response=response)

        
        

