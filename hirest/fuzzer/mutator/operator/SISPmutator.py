import random, logging

from typing import Any

from hirest.model.testcase import TestCase
from hirest.model.sisp import SISP, SISP_SS
from hirest.model.misp import Subspace, MixedSingleSpace

from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.fuzzer.mutator.operator.mutator import Mutator

logger = logging.getLogger(__name__)


class SISPMutator(Mutator):
    """SISPMutator class: mutate the Test Case by mutating a SISP for a single parameter."""

    def valid_mutate(self, testcase:TestCase, **kwargs) -> TestCase:
        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        site = kwargs.get("site")
        
        # Validate the arguments for mutation
        if not self._validate_args(testcase, input_space_manager=input_space_manager, site=site):
            logger.warning("Invalid arguments for SISP mutation, terminating mutation.")
            return testcase
        
        logger.debug(f"Validated arguments for SISP mutation site: {site}")
        
        # select a new SISP_SS site for mutation
        new_sisp_ss = self._select_new_sisp_ss(
            input_space_manager=input_space_manager,
            testcase=testcase,
            sisp_ss=site,
            type="valid",
        )

        logger.debug(f"Selected new SISP_SS for SISP mutation: {new_sisp_ss}")
        
        testcase = self._update_sisp_ss(
            testcase=testcase,
            sisp_ss=site,
            new_sisp_ss=new_sisp_ss,
        )

        return testcase

    def destroy_mutate(self, testcase:TestCase, **kwargs)-> TestCase:
        """Perform a destroy mutation on the test case."""
        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        site = kwargs.get("site")

        # Validate the arguments for mutation
        if not self._validate_args(testcase, input_space_manager=input_space_manager, site=site):
            logger.warning("Invalid arguments for SISP mutation, terminating mutation.")
            return testcase

        logger.debug(f"Validated arguments for SISP mutation site: {site}")

        # select a new SISP_SS site for mutation
        new_sisp_ss = self._select_new_sisp_ss(
            input_space_manager=input_space_manager,
            testcase=testcase,
            sisp_ss=site,
            type="invalid",
        )

        logger.debug(f"Selected new SISP_SS for SISP mutation: {new_sisp_ss}")

        testcase = self._update_sisp_ss(
            testcase=testcase,
            sisp_ss=site,
            new_sisp_ss=new_sisp_ss,
        )

        return testcase
        
    def select_site(self, testcase: TestCase) -> SISP_SS | None:
        """Select a mutation site (SISP_SS) for mutation in the test case."""

        sisp_ss = random.choice(testcase.matched_SISP)
        return sisp_ss
    
    def _validate_args(
        self,
        testcase:TestCase,
        **kwargs,
    ) -> bool:
        """Validate the arguments (inputspacemanager, sisp_site) for the mutation."""
        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        site:SISP_SS = kwargs.get("site")

        if not input_space_manager:
            logger.warning("Input space manager is not provided.")
            return False
        if not testcase.matched_SISP:
            logger.warning("No SISP spaces matched is found in the test case.")
            return False
        
        if not site:
            logger.warning("No SISP_SS site is provided.")
            return False
        if site not in testcase.matched_SISP:
            logger.warning(
                f"The selected SISP_SS site {site} is not in the matched SISP spaces."
            )
            return False

        return True

    def _select_new_sisp_ss(
        self,
        input_space_manager: InputSpaceManager,
        testcase: TestCase,
        sisp_ss: SISP_SS,
        type: str
    ) -> SISP_SS:
        """Select a new SISP_SS for mutation."""

        if type not in ["valid", "invalid"]:
            logger.warning(
                f"Invalid type '{type}' for SISP mutation. Expected 'valid' or 'invalid'."
            )
            return testcase
            
        op_name = testcase.operation.op_name
        param_name = sisp_ss.param_name

        mss = testcase.query_mixed_subspace_by_param(param_name, type)

        if mss == []:
            logger.warning(
                f"No MixedSingleSpace found for operation '{op_name}' and parameter '{param_name}' in subspace."
            )
            return None

        # avoid selecting the same category as the original SISP_SS
        selectable_categories = []
        for item in mss:
            if item.input_space_category != sisp_ss.category:
                selectable_categories.append(item.input_space_category)
        
        if len(selectable_categories) == 0:
            logger.warning(
                f"No selectable categories found for operation '{op_name}' and parameter '{param_name}'."
            )
            return sisp_ss
        
        choice = random.choice(selectable_categories)
        new_sisp_ss = input_space_manager.sisps[op_name][
            param_name
        ].select_ss_by_category(choice)

        return new_sisp_ss
    
    def _update_sisp_ss(
        self,
        testcase: TestCase,
        sisp_ss: SISP_SS,
        new_sisp_ss: SISP_SS,
    ) -> TestCase:
        """Update the SISP_SS in the test case."""
        testcase.matched_SISP.remove(sisp_ss)
        testcase.matched_SISP.append(new_sisp_ss)

        return testcase