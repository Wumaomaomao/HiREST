from abc import ABC, abstractmethod

from hirest.model.testcase import TestCase

from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.fuzzer.mutator.operator.mutator import Mutator
from hirest.fuzzer.mutator.strategy import SISPSelectStrategy, SelectStrategy


class MutationController(ABC):
    """
    Abstract base class for mutation controllers.
    mutation controller is responsible for scheduling and executing mutations on the testcase.

    2025-04-16  notes about mutation design
    It can be used to implement different mutation strategies, which may be differ in the following aspects:
    1. Mutation **magnitude**: the number of mutations to be applied to the testcase.
    2. Mutation **operator** (mutator) selection: the mutator to be used for the mutation.
    3. Mutation **site**: the location of the mutation in the testcase.
    """

    def __init__(
        self,
        input_space_manager: InputSpaceManager,
        mutators: list[Mutator],
        select_strategy: SelectStrategy = None,
    ):
        """
        Initialize the MutationController with an InputSpaceManager.
        Args:
            input_space_manager (InputSpaceManager): The input space manager to be used.
            mutators (list[Mutator]): List of available mutators.
            select_strategy (SelectStrategy): The strategy to select the mutator.
        """
        self.input_space_manager = input_space_manager
        self.mutators = mutators
        self.select_strategy = select_strategy

    @abstractmethod
    def load_strategy(self, strategy: dict):
        """
        Load a mutation strategy.
        Args:
            strategy (dict): The mutation strategy to be loaded.
        """

        raise NotImplementedError(
            "MutationController `load_strategy` method not implemented"
        )

    @abstractmethod
    def mutate(self, testcase: TestCase) -> TestCase:
        """
        Mutate the testcase and return the mutated testcase.
        Args:
            testcase (TestCase): The original testcase to be mutated.
        Returns:
            TestCase: The mutated testcase.
        """
        raise NotImplementedError("MutationController `mutate` method not implemented")