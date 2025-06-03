from hirest.fuzzer.mutator.strategy import SelectStrategy, SISPSelectStrategy
from hirest.fuzzer.mutator.controller.basic_controller import BasicMutationController


class SISPMutationController(BasicMutationController):
    """
    SISPMutationController is a specialized mutation controller that applies SISP mutations to the testcase.
    It uses a specific selection strategy to choose the mutators and manages the mutation process.
    """

    def __init__(
        self,
        input_space_manager,
        mutators,
        select_strategy: SelectStrategy = SISPSelectStrategy(),
    ):
        """
        Initialize the SISPMutationController with an InputSpaceManager.
        Args:
            input_space_manager (InputSpaceManager): The input space manager to be used.
            mutators (list[Mutator]): List of available mutators.
            select_strategy (SelectStrategy): The strategy to select the mutator.
        """
        super().__init__(input_space_manager, mutators, select_strategy)