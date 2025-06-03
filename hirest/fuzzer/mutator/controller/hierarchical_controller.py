import logging
from typing import Any

from hirest.fuzzer.mutator.operator.mutator import Mutator
from hirest.fuzzer.mutator.controller.controller import MutationController
from hirest.fuzzer.mutator.controller.sisp_controller import SISPMutationController
from hirest.fuzzer.mutator.controller.misp_controller import MISPMutationController
from hirest.fuzzer.mutator.controller.sequential_controller import SequentialMutationController

logger = logging.getLogger(__name__)

class HierarchicalMutationController(SequentialMutationController):
    """
    Hierarchical mutation controller that applies different mutations (controller) to the testcase in a Sequential controller.
    """

    def __init__(self, input_space_manager, mutators, select_strategy=None, **kwargs):
        """
        Initialize the HierarchicalMutationController with an InputSpaceManager.
        Args:
            input_space_manager (InputSpaceManager): The input space manager to be used.
            mutators (list[Mutator]): List of available mutators.
        """
        mutation_controllers:list[MutationController] = [
            MISPMutationController(input_space_manager, mutators),
            SISPMutationController(input_space_manager, mutators)
        ]
        super().__init__(input_space_manager, mutators, select_strategy, mutation_controllers=mutation_controllers,**kwargs)
