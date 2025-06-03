from hirest.fuzzer.mutator.controller.basic_controller import BasicMutationController
from hirest.fuzzer.mutator.strategy import SelectStrategy, MISPSelectStrategy


class MISPMutationController(BasicMutationController):
    """
    MISP mutation controller that applies MISP mutations to the testcase.
    """

    def __init__(
        self,
        input_space_manager,
        mutators,
        select_strategy: SelectStrategy = MISPSelectStrategy(),
    ):
        """
        Initialize the MISP mutation controller with an InputSpaceManager.
        Args:
            input_space_manager (InputSpaceManager): The input space manager to be used.
            mutators (list[Mutator]): List of available mutators.
            select_strategy (SelectStrategy): The strategy to select the mutator.
        """
        super().__init__(input_space_manager, mutators, select_strategy)
    