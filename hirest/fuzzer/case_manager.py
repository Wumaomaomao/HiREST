from enum import Enum
import random, logging, json
from typing import Any
from collections import deque

from hirest.model.parameter import Parameter
from hirest.model.operation import Operation
from hirest.model.misp import MISP, MISP_SS
from hirest.model.testcase import TestCase, TestCasePool, MutationType

from hirest.fuzzer.input_space_manager import InputSpaceManager

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """sequence execution mode: EXTEND or DESTROY"""

    EXTEND = "extend"
    DESTROY = "destroy"

    """
    EXTEND: replay the history requests sequence from `seqs` without any mutation and try to extend the sequence \
      with a new testcase (and mutate it) after the last testcase"""

    """
    DESTROY: execute the history sequence from `maxlen_seqs` as follows : 
        ( prob = 1 / len(seq) )
    
        1. prob : execute the history testcase from exec_seq with destory mutation \
        2. 1 - prob : replay the history request from exec_seq without any mutation 

    """


class CaseManager:
    """case manager class: responsible for managing the test cases and the sequence."""

    def __init__(
        self,
        input_space_manager: InputSpaceManager,
        max_sequence_length: int = 5,
        max_extend_try=3,
        max_candidate_seq=5,
        destory_ratio=0.2,
    ):
        """initialize the case manager with the test case pool and the sequence."""
        self.max_sequence_length = max_sequence_length
        self.input_space_manager = input_space_manager

        self.operations: dict[str, Operation] = {}
        self.case_pools: dict[str, TestCasePool] = {}

        self.seqs: list[list[TestCase]] = [
            list[TestCase]() for _ in range(max_candidate_seq)
        ]
        """successfully executed sequences of test cases"""
        self.exec_seq: list[TestCase] = []
        """list of test cases to be executed"""
        self.exec_pointer = -1
        """exec_pointer: the pointer of the current test case in the exec_seq"""
        self.retry_count = 0
        """retry count for the test case execution when the response is not valid"""
        self.max_extend_retry = max_extend_try

        self.exec_mode = "extend"

        self.maxlen_seqs: list[TestCase] = []
        """collection of sequences, each sequence is a list of test cases to be mutated to invalid test cases"""

        self.destory_ratio = destory_ratio
        """the ratio of selecting maxlen sequence to be destroyed in the process of initializing the exec_seq"""

    def load_operations(self, operations: list[dict[str, Any]]) -> None:
        """load the operations and create the test case pools."""
        for operation in operations:
            try:
                operation["param_list"] = [
                    Parameter(**param) for param in operation["param_list"]
                ]
                op_model = Operation(**operation)
                self.operations[op_model.op_name] = op_model
            except Exception as e:
                logger.error(f"Failed to load operation: {operation}, error: {e}")

            logger.debug(
                f"Load operation: {op_model.op_name}, operation model: {self.operations[op_model.op_name]}"
            )

        self._init_case_pools()

    def _init_case_pools(self) -> None:
        """initialize the test case pools for each operation."""
        for op_name in self.operations:
            self.case_pools[op_name] = TestCasePool(
                operation=self.operations[op_name], max_size=1000
            )
            logger.debug(f"Init case pool: {self.case_pools[op_name]}")

    def load_seeds(self, seed_data: list[dict[str, Any]]) -> None:
        """load the seeds from seed_data and convert them to TestCase."""

        for seed in seed_data:
            try:
                op_name = seed["op_name"]
                matched_misp, matched_subspace = self.input_space_manager.get_misp_ss(
                    op_name, seed["selected_spaces"]
                )
                matched_sisp = self.input_space_manager.get_sisp_ss(
                    op_name, seed["selected_parameters_list"]
                )
                testcase: TestCase = TestCase(
                    operation=self.operations[op_name],
                    matched_MISP=matched_misp,
                    matched_Subspace=matched_subspace,
                    matched_SISP=matched_sisp,
                )
                self.case_pools[op_name].add_testcase(testcase)
                logger.debug(f"Load seed: {seed}, testcase: {testcase}")
            except Exception as e:
                logger.error(f"Failed to load seed: {seed}, error: {e}", exc_info=True)

                
    def _init_exec_seq(self) -> list[TestCase]:
        """initialize the exec_seq with self.seqs when exec_seq is empty."""
        if self.maxlen_seqs and random.random() < self.destory_ratio:
            self.exec_mode = ExecutionMode.DESTROY
            # purpose: destructive case execution
            # select a sequence from the maxlen_seqs to be destroyed
            exec_seq = random.choice(self.maxlen_seqs)[:]

        else:
            self.exec_mode = ExecutionMode.EXTEND
            # purpose: extended sequence execution
            # select a sequence from the seqs to be executed and try to extend it
            exec_seq = random.choice(self.seqs)[:]

        # # [**] ablation hierarchical mutation (destory mutation)
        # self.exec_mode = ExecutionMode.EXTEND
        # # purpose: extended sequence execution
        # # select a sequence from the seqs to be executed and try to extend it
        # exec_seq = random.choice(self.seqs)[:]

        self.exec_pointer = 0
        self.retry_count = 0

        logger.debug(
            f"exec_mode: {self.exec_mode} init exec_seq: {exec_seq}, exec_pointer: {self.exec_pointer}, retry_count: {self.retry_count}"
        )
        return exec_seq

    def _try_extend_seq(self) -> TestCase:
        """extend the exec_seq with the next testcase."""

        # if the case is already in the exec_seq, it means that the case is already executed
        # to avoid too many duplicated cases, we will retry to extend the exec_seq ...
        for _ in range(5):
            op = self.next_operation()
            case = self._sample_case(op)
            if case not in self.exec_seq:
                break
            else:
                logger.debug(
                    f"try to extend seq, but {case} is already in the exec_seq, retry to extend"
                )

        self.exec_pointer = -1
        self.retry_count += 1
        logger.debug(f"try to extend seq, {case} is selected to be executed")
        return case

    def _sample_case(self, op: Operation) -> TestCase:
        """select a testcase for the operation from the case pool."""
        return (
            TestCase.derive(random.choice(self.case_pools[op.op_name].testcases))
            if self.case_pools[op.op_name].testcases
            else None
        )

    def next_testcase(self) -> tuple[TestCase, bool]:
        """return the next testcase to be executed considering the sequences."""

        "1. extend mode : failed to extend the exec_seq ,so we need to archive the exec_seq"
        if (
            self.exec_mode == ExecutionMode.EXTEND
            and self.exec_pointer == -1
            and self.retry_count >= self.max_extend_retry
            and self.exec_seq != None
        ):
            "if retry_count >= max_extend_retry, it means that extended is failed, exec_seq will be archived"
            self._archive_seq()
        "2. destroy mode: exec_seq has been executed, so we need to reset the exec_seq"
        if (self.exec_mode == ExecutionMode.DESTROY
            and self.exec_pointer >= len(self.exec_seq)
        ):
            """if exec_pointer >= len(exec_seq), it means that the seq is already executed, \
                so we need terminate the exec_seq by reset the exec_seq"""
            logger.debug(
                f"exec_pointer: {self.exec_pointer} is out of range, exec_seq is \
                         already executed with destory mode, so we need to reset the exec_seq"
            )
            self._reset_exec_seq()

        if not self.exec_seq:
            "if exec_seq is None, it means that the exec_seq is empty, so we need to init it"
            self.exec_seq = self._init_exec_seq()

        if self.exec_pointer <= len(self.exec_seq) - 1:
            logger.debug(
                f"Move the exec_pointer to the next case: {self.exec_pointer},\
                    \n request: {self.exec_seq[self.exec_pointer].request}"
            )
            match self.exec_mode:
                case ExecutionMode.EXTEND:
                    "execute a sucess case, so you don't need modify the testcase"
                    testcase = self.exec_seq[self.exec_pointer]
                    self.exec_pointer += 1
                    return [testcase, False]
                case ExecutionMode.DESTROY:
                    testcase = self.exec_seq[self.exec_pointer]
                    self.exec_pointer += 1
                    prob = 1 / len(self.exec_seq)
                    logger.debug(f"testcase mutate prob: {prob}")
                    if random.random() < prob:
                        logger.debug(
                            f"testcase {self.exec_pointer} of exec_seq is selected to be destroyed"
                        )
                        testcase.mutation_type = MutationType.DESTROY
                        return [testcase, True]
                    else:
                        logger.debug(
                            f"testcase {self.exec_pointer} of exec_seq is not selected to be destroyed"
                        )
                        return [testcase, False]
                case _:
                    logger.error(f"Invalid exec_mode: {self.exec_mode}")
                    return [None, False]

        elif self.exec_pointer == len(self.exec_seq) or (
            self.retry_count < self.max_extend_retry and self.exec_pointer == -1
        ):
            match self.exec_mode:
                case ExecutionMode.EXTEND:
                    testcase = self._try_extend_seq()
                    return [testcase, True]
                    "try a new case, so you need mutate the testcase"

        raise ValueError(
            f"Invalid exec_pointer: {self.exec_pointer} for current exec_seq: {self.exec_seq} \
                with exec_mode: {self.exec_mode}"
        )

    def next_operation(self) -> Operation:
        """return the next operation to be execuated considering the sequences."""

        return random.choice(list(self.operations.values()))

    def _reset_exec_seq(self) -> None:
        """reset the exec_seq to None."""
        self.exec_seq = None
        self.exec_pointer = -1

    def _archive_seq(self) -> None:
        """archive the exec_seq to the seqs."""
        if len(self.exec_seq) > self.max_sequence_length:
            "if len > max_sequence_length, it means that the exec_seq is too long"
            self.maxlen_seqs.append(self.exec_seq[:])
            logger.debug(
                f"Archive the maxlen_seqs: {self.maxlen_seqs} has been archived for maxlen_seqs"
            )
        else:
            self.seqs.append(self.exec_seq[:])
            logger.debug(
                f"Archive the exec_seq (length = {len(self.exec_seq)}): {self.exec_seq} has been archived"
            )

        self._reset_exec_seq()

    def _extend_seq(self, testcase: TestCase) -> None:
        """extend the exec_seq with the next testcase."""
        if self.exec_pointer == -1:
            # if the exec_pointer is -1, it means that the testcase is newly extended
            self.exec_seq.append(testcase)
            self._archive_seq()
        else:
            raise ValueError(
                f"Invalid exec_pointer: {self.exec_pointer} for invoking _extend_seq()"
            )

    def handle_execution(self, testcase: TestCase, response: dict[str, Any]) -> None:
        """handle the execution of the test case and update the sequence."""
        if self.exec_mode == ExecutionMode.EXTEND and self.exec_pointer == -1:
            # if the exec_pointer is -1, it means that the testcase is newly extended
            if response["status_code"] >= 200 and response["status_code"] < 300:
                # sucessfully execution
                if (
                    testcase
                    not in self.case_pools[testcase.operation.op_name].testcases
                ):
                    self.case_pools[testcase.operation.op_name].add_testcase(testcase)
                    logger.debug(
                        f"Add successfully executed testcase to the pool: {testcase.operation.op_name}, testcase: {testcase}"
                    )

                self._extend_seq(testcase)
            else: 
                self.input_space_manager.update_sisp_ss_failure_count(testcase.operation, testcase.matched_SISP)
    

