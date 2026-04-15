import logging, random
from typing import Optional

from hirest.utils.random_generator import random_gen_integer, random_gen_number, random_gen_string, random_gen_boolean

from hirest.model.testcase import TestCase
from hirest.model.operation import Operation
from hirest.model.parameter import Parameter

from hirest.fuzzer.mutator.operator.mutator import Mutator

logger = logging.getLogger(__name__)

class WrongTypeMutator(Mutator):
    
    def valid_mutate(self, testcase, **kwargs):
        """
        no valid mutation"""
        logger.warning("No valid mutation implementation for WrongTypeMutator.")
        return testcase
    
    def destroy_mutate(self, testcase:TestCase, **kwargs):
        """
        Apply an invalid mutation to the test case.
        This method should be overridden by subclasses to implement specific mutation logic.
        """
        site = kwargs.get("site")
        
        if not self._validate_args(testcase, site=site):
            logger.warning("Invalid arguments for mutation.")
            return testcase
        
        parameter = testcase.operation.query_param_by_name(site)
        
        if not parameter:
            logger.warning(f"Parameter {site} not found in operation {testcase.operation.op_name}.")
            return testcase
        
        param_val_type = parameter.val_type
        val_type_pools = ["integer", "number", "string", "boolean"]

        if param_val_type not in val_type_pools:
            logger.warning(f"Parameter {site} has an unsupported type: {param_val_type}.")
            return testcase
        
        optional_type_pools = val_type_pools.copy()
        optional_type_pools.remove(param_val_type)
        new_val_type = random.choice(optional_type_pools)

        match new_val_type:
            case "integer":
                new_val = random_gen_integer()
            case "number":
                new_val = random_gen_number()
            case "string":
                new_val = random_gen_string()
            case "boolean":
                new_val = random_gen_boolean()
        
        testcase.param_vals[site] = new_val
        logger.debug(f"Changing {site} from {param_val_type} to {new_val_type}: {new_val}")

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