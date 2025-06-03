import logging

from hirest.fuzzer.mutator.controller.controller import MutationController

logger = logging.getLogger(__name__)

class SequentialMutationController(MutationController):
    """
    Sequential mutation controller that applies different mutations (controller) to the testcase in a pipline.
    """

    def __init__(self, input_space_manager, mutators, select_strategy=None, **kwargs):
        """
        Initialize the SequentialMutationController with an InputSpaceManager.
        Args:
            input_space_manager (InputSpaceManager): The input space manager to be used.
            mutators (list[Mutator]): List of available mutators.
        """
        super().__init__(input_space_manager, mutators, select_strategy)

        self.mutation_controllers:list[MutationController] = kwargs.get("mutation_controllers")
        if self.mutation_controllers is None:
            raise ValueError("mutation_controllers must be provided, you need to config a list of mutation controllers for pipline")

    def load_strategy(self, strategy: dict):
        return
    
    def mutate(self, testcase):
        """
        Mutate the testcase and return the mutated testcase.
        Args:
            testcase (TestCase): The original testcase to be mutated.
        Returns:
            TestCase: The mutated testcase.
        """
        for controller in self.mutation_controllers:
            logger.debug(f"enter mutation controller: {controller.__class__.__name__}")
            testcase = controller.mutate(testcase)
            logger.debug(f"exit mutation controller, mutated testcase: {testcase}")
        
        return testcase
