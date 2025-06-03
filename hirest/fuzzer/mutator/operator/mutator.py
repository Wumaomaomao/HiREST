import logging
from typing import Any
from abc import ABC, abstractmethod

from hirest.model.testcase import TestCase, MutationType
logger = logging.getLogger(__name__)

class Mutator(ABC):
    """Mutator class: Abstract base class for mutation operators (mutators)."""
    


    def mutate(self, testcase: TestCase, **kwargs) -> TestCase:
        """Mutate the test case and return the mutated test case.
        according to the mutation type of the testcase, \
          we will use different method to mutate the testcase.
        Args:
            testcase (TestCase): The original test case to be mutated.
            **kwargs: Additional arguments for the mutation process.
        Returns:
            TestCase: The mutated test case.
        
        """
        match testcase.mutation_type:
            case MutationType.NORMAL:
                logger.debug("perform normal mutation")
                return self.valid_mutate(
                    testcase, **kwargs
                )
            case MutationType.DESTROY:
                logger.debug("perform destroy mutation")
                return self.destroy_mutate(
                    testcase, **kwargs
                )
            case _:
                raise ValueError(
                    f"Unknown mutation type: {testcase.mutation_type}"
                )

    @abstractmethod
    def valid_mutate(
        self, testcase: TestCase, site: Any, **kwargs
    ) -> bool:
        """Check if the mutation is valid."""
        
        raise NotImplementedError("Mutator `valid_mutate` method not implemented")
    
    @abstractmethod
    def destroy_mutate(
        self, testcase: TestCase, site: Any, **kwargs
    ) -> TestCase:
        """Perform a destroy mutation on the test case."""
        
        raise NotImplementedError("Mutator `destory_mutate` method not implemented")
        