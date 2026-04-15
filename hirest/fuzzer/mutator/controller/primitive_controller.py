

from hirest.fuzzer.mutator.controller.basic_controller import BasicMutationController
from hirest.fuzzer.mutator.strategy import PrimitiveSelectStrategy

class PrimitiveMutationController(BasicMutationController):
    """
    Primitive mutation controller that applies three basic mutations (value perturbation, \
    wrongtype, missing required) to the testcase.
    """

    def __init__(self, input_space_manager, mutators, select_strategy=None, **kwargs):
        """
        Initialize the PrimitiveMutationController with an InputSpaceManager.
        Args:
            input_space_manager (InputSpaceManager): The input space manager to be used.
            mutators (list[Mutator]): List of available mutators.
        """
        if select_strategy is None:
            select_strategy = PrimitiveSelectStrategy()
        super().__init__(input_space_manager, mutators, select_strategy)