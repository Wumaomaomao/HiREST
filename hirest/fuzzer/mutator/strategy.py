import random, logging
from abc import ABC, abstractmethod
from typing import Tuple, Any

from hirest.model.misp import MISP, MISP_SS, Subspace
from hirest.model.sisp import SISP, SISP_SS
from hirest.model.testcase import TestCase, MutationType

from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.fuzzer.mutator.operator.mutator import Mutator
from hirest.fuzzer.mutator.operator.SISPmutator import SISPMutator
from hirest.fuzzer.mutator.operator.MISPmutator import MISPMutator
from hirest.fuzzer.mutator.operator.MISPSSmutator import MISPSSMutator
from hirest.fuzzer.mutator.operator.perturbation_mutator import PerturbationMutator
from hirest.fuzzer.mutator.operator.wrongtype_mutator import WrongTypeMutator
from hirest.fuzzer.mutator.operator.missingrequired_mutator import MissingRequiredMutator

logger = logging.getLogger(__name__)


class SelectStrategy(ABC):
    @abstractmethod
    def select_mutator(self, mutators: list[Mutator], **kwargs) -> list[Mutator] | list[Tuple[Mutator, Any]]:
        """
        This is a abstract method that should be implemented by subclasses to select mutators.
        argument `mutators` is a list of available mutators.
        """
        raise NotImplementedError(
            "SelectStrategy `select_mutator` method not implemented"
        )

class MISPSelectStrategy(SelectStrategy):
    def select_mutator(self, mutators: list[Mutator], **kwargs) -> list[Tuple[Mutator, Any]]:
        """
        Select MISP mutation sites and mutators for the given test case.

        Args:
            mutators (list[Mutator]): List of available mutators.

        Returns:
            list[Tuple[Mutator, Any]]: List of tuples containing the selected mutator and the corresponding MISP_SS.
        """

        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        testcase: TestCase = kwargs.get("testcase")

        if not input_space_manager:
            raise ValueError("Input space manager is not provided.")
        if not testcase:
            raise ValueError("Test case is not provided.")

        global_searchable_misp = input_space_manager.misps[testcase.operation.op_name]
        misp_mutate_prob = 1 / len(global_searchable_misp.space_list)
        logger.debug(f"misp_mutate_prob: {misp_mutate_prob}")
        selected_misp_ss: list[MISP_SS] = []
        for misp_ss in global_searchable_misp.space_list:
            if random.random() < misp_mutate_prob:
                selected_misp_ss.append(misp_ss)
        logger.debug(
            f"Selected MISP_SS spaces for mutation: {[misp_ss.space_name for misp_ss in selected_misp_ss]}"
        )
        
        selected_result = list[Tuple[Mutator, Any]]()
        for misp_ss in selected_misp_ss:
            if misp_ss in testcase.matched_MISP:
                # If the MISP_SS already exists in the test case, we can either remove it or change it
                if random.random() < 0.5:
                    # Remove the MISP_SS
                    selected_result.append((MISPMutator(), misp_ss))
                else:
                    # Change the MISP_SS
                    selected_result.append((MISPSSMutator(), testcase.matched_Subspace.get(misp_ss.space_name)))
            else:
                # If the MISP_SS does not exist, we can add it
                selected_result.append((MISPMutator(), misp_ss))

        return selected_result

class SISPSelectStrategy(SelectStrategy):
    def select_mutator(self, mutators: list[Mutator], **kwargs) -> list[tuple[Mutator, Any]]:
        """
        Select SISP mutation sites and mutators for the given test case.

        Args:
            mutators (list[Mutator]): List of available mutators.

        Returns:
            list[tuple[Mutator, Any]]: List of tuples containing the selected mutator and the corresponding SISP_SS.
        """

        testcase: TestCase = kwargs.get("testcase")

        if not testcase:
            raise ValueError("Test case is not provided.")
        
        if not testcase.matched_SISP:
            logger.warning("No matched SISP spaces of SISP_SS matched is found in the test case.")
            return []

        searchable_sisp = testcase.matched_SISP
        sisp_mutate_prob = 1 / len(searchable_sisp)
        logger.debug(f"sisp_mutate_prob: {sisp_mutate_prob}")
        selected_sisp_ss: list[SISP_SS] = []
        for sisp_ss in searchable_sisp:
            if random.random() < sisp_mutate_prob:
                selected_sisp_ss.append(sisp_ss)
        logger.debug(
            f"Selected SISP_SS spaces for mutation: {[sisp_ss.category for sisp_ss in selected_sisp_ss]}"
        )

        selected_result = [(SISPMutator(), sisp_ss) for sisp_ss in selected_sisp_ss]

        return selected_result


class PrimitiveSelectStrategy(SelectStrategy):
    def select_mutator(self, mutators: list[Mutator], **kwargs) -> list[tuple[Mutator, Any]]:
        """
        Select mutators for the given test case.

        Args:
            mutators (list[Mutator]): List of available mutators.

        Returns:
            list[tuple[Mutator, Any]]: The selected mutator-site pairs.
        """

        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        testcase: TestCase = kwargs.get("testcase")

        if not input_space_manager:
            raise ValueError("Input space manager is not provided.")
        if not testcase:
            raise ValueError("Test case is not provided.")

        param_count = len(testcase.param_vals)

        if param_count == 0:
            logger.warning("No parameters found in the test case.")
            return []

        mutate_prob = 1 / param_count
        logger.debug(f"mutate_prob: {mutate_prob}")

        selected_result: list[tuple[Mutator, Any]] = []

        for param_name in list(testcase.param_vals.keys()):
            if random.random() < mutate_prob:
                match testcase.mutation_type:
                    case MutationType.NORMAL:
                        selected_result.append((PerturbationMutator(), param_name))
                    case MutationType.DESTROY:
                        roulette = random.random()
                        if roulette < (1 / 3):
                            selected_result.append((WrongTypeMutator(), param_name))
                        elif roulette < (2 / 3):
                            selected_result.append((MissingRequiredMutator(), param_name))
                        else:
                            selected_result.append((PerturbationMutator(), param_name))

        return selected_result

