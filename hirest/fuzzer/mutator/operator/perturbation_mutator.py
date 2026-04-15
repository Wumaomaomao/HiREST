from hmac import new
import logging, random

from hirest.model.operation import Operation
from hirest.model.testcase import TestCase

from hirest.fuzzer.mutator.operator.mutator import Mutator

logger = logging.getLogger(__name__)

class PerturbationMutator(Mutator):
    """
    PerturbationMutator is a class that implements a mutator for fuzzing.
    It applies perturbations to the input data to generate new test cases.
    """
    
    def valid_mutate(self, testcase:TestCase, **kwargs):
        """
        Apply a valid perturbation to the test case.
        This method should be overridden by subclasses to implement specific perturbation logic.
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
        param_val = testcase.param_vals[site]

        # perform perturbation based on the parameter type: (integer, number, string, boolean)
        match param_val_type:
            case "integer":
                new_val = (str)(self._integer_perturbation(int(param_val)))
            case "number":
                new_val = (str)(self._number_perturbation(float(param_val)))
            case "string":
                new_val = (self._string_perturbation(str(param_val)))
            case "boolean":
                new_val = (str)(self._boolean_perturbation(bool(param_val)))
            case _:
                logger.warning(f"Unsupported parameter type: {param_val_type}")
                return testcase
            
        testcase.param_vals[site] = new_val
        logger.debug(f"Perturbing {site} from {param_val} to {new_val}")

        return testcase   
    
    def destroy_mutate(self, testcase:TestCase, **kwargs):
        """
        Apply an invalid perturbation to the test case.
        This method should be overridden by subclasses to implement specific perturbation logic.
        """
        return self.valid_mutate(testcase, **kwargs)
    
    def _validate_args(self, testcase:TestCase, **kwargs):
        """
        Validate the arguments for mutation.

        """
        site = kwargs.get("site")

        if not site:
            logger.warning("No site provided for mutation.")
            return False

        if site not in list(testcase.param_vals.keys()):
            logger.warning(f"Site {site} not found in test case parameters.")
            return False
        
        return True

    def _integer_perturbation(self, prev_val:int) -> int:
        """
        Apply an integer perturbation to the test case.
        """

        delta = random.randint(0, 30)

        delta_val = 2 ** delta

        if random.random() < 0.5:
            new_val = prev_val + delta_val
        else:
            new_val = prev_val - delta_val

        return new_val
    
    def _number_perturbation(self, prev_val:float) -> float:

        """
        Apply a number perturbation to the test case.
        """

        delta = random.randint(0, 30)

        delta_val = 2 ** delta 

        delta_val = delta_val * random.gauss(0, 1)
        

        if random.random() < 0.5:
            new_val = prev_val + delta_val
        else:
            new_val = prev_val - delta_val

        return new_val
    
    def _string_perturbation(self, prev_val:str) -> str:

        """
        Apply a string perturbation to the test case.
        1. append a random character to the string
        2. update a random character from the string
        3. drop the last character from the string 
        """
        printable_ascii = ''.join([chr(i) for i in range(32, 127)])
        randomchars = printable_ascii

        new_val = prev_val
        if random.random() < 1/3:
            # append a random character to the string
            new_val = prev_val + random.choice(randomchars)
        elif random.random() < 1/2 and len(prev_val) > 0:
            # update a random character from the string
            index = random.randint(0, len(prev_val) - 1)
            old_char = prev_val[index]
            delta = random.choice([-1, 1])
            new_char = chr(max(32, min(126, ord(old_char) + delta)))
            new_val = prev_val[:index] + new_char + prev_val[index + 1:]
        else:
            # drop the last character from the string
            new_val = prev_val[:-1]

        return new_val 

    def _boolean_perturbation(self, prev_val:bool) -> bool:
        """
        Apply a boolean perturbation to the test case.
        """
        new_val = not prev_val
        return new_val       