from typing import Any

from hirest.fuzzer.mutator.controller.controller import MutationController
from hirest.fuzzer.mutator.strategy import SelectStrategy

from hirest.fuzzer.mutator.operator.mutator import Mutator

from hirest.model.testcase import TestCase

class BasicMutationController(MutationController):
    """
    Basic Mutation Controller select mutators and sites as **SelectStrategy**(e.g. SISPSelectStrategy) and \
    just execute the mutators on the selected sites sequentially 
    """

    def __init__(
        self,
        input_space_manager,
        mutators,
        select_strategy: SelectStrategy,
    ):
        """
        Initialize the BasicMutationController with an InputSpaceManager.
        Args:
            input_space_manager (InputSpaceManager): The input space manager to be used.
            mutators (list[Mutator]): List of available mutators.
            select_strategy (SelectStrategy): The strategy to select the mutator.
        """
        super().__init__(input_space_manager, mutators, select_strategy)

    def load_strategy(self, strategy):
        return 
    
    def mutate(self, testcase:TestCase)-> TestCase:
        """
        Mutate the testcase and return the mutated testcase.
        Args:
            testcase (TestCase): The original testcase to be mutated.
        Returns:
            TestCase: The mutated testcase.
        """
        selected_mutators = []
        selected_sites = []

        selected_result:list[tuple[Mutator, Any]] = self.select_strategy.select_mutator(
            self.mutators,
            input_space_manager=self.input_space_manager,
            testcase=testcase,
        )
        
        for mutator, site in selected_result:
            mutator.mutate(
                testcase, input_space_manager=self.input_space_manager, site=site
            )

        return testcase
    
    