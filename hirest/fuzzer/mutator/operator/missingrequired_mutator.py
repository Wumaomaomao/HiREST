import logging

from hirest.model.testcase import TestCase
from hirest.model.operation import Operation
from hirest.model.parameter import Parameter

from hirest.fuzzer.mutator.operator.mutator import Mutator

logger = logging.getLogger(__name__)

class MissingRequiredMutator(Mutator):
    
    def valid_mutate(self, testcase, **kwargs):
        """
        no valid mutation"""
        logger.warning("No valid mutation implementation for MissingRequiredMutator.")
        return testcase
    
    def destroy_mutate(self, testcase, **kwargs):
        """
        Apply an invalid mutation to the test case.
        This method should be overridden by subclasses to implement specific mutation logic.
        """
        site = kwargs.get("site")
        
        if not self._validate_args(testcase, site=site):
            logger.warning("Invalid arguments for mutation.")
            return testcase
        
        parameter = testcase.operation.query_param_by_name(site)
        if parameter.is_required:
            testcase.param_vals.pop(site)
            logger.debug(f"Removing the required parameter {site} from test case.")
        else:
            logger.warning(f"Parameter {site} is not required, no mutation applied.")
        
        return testcase
    
    def _validate_args(self, testcase, **kwargs):
        """
        Validate the arguments for the mutation.
        """
        site = kwargs.get("site")
        
        if not site:
            logger.warning("Missing required argument: site.")
            return False
        
        if not testcase:
            logger.warning("Missing required argument: testcase.")
            return False
        
        if site not in list(testcase.param_vals.keys()):
            logger.warning(f"Site {site} not found in test case parameters.")
            return False
        
        return True
