import random, logging

from hirest.model.testcase import TestCase
from hirest.model.misp import MISP, MISP_SS, Subspace
from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.fuzzer.mutator.operator.mutator import Mutator

logger = logging.getLogger(__name__)


class MISPMutator(Mutator):
    """MISPMutator class: Mutate the Test Case by mutating MISP for an operation."""
    
    def valid_mutate(
        self, testcase: TestCase, **kwargs
    ) -> TestCase:
        """Check if the mutation is valid."""
        # Check if the site is in the matched MISP spaces of the test case
        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        site: MISP_SS = kwargs.get("site")

        if not input_space_manager:
            logger.warning("Input space manager is not provided.")
            return testcase
        
        if not site:
            logger.warning("No MISP_SS site is provided.")
            return testcase
    
        if site in testcase.matched_MISP:
            if site and site.satisfied_dependencies == "Minimum input space.":
                logger.debug(
                    f"skip the minimum input space for MISP_SS site: {site}"
                )
            else:
                self._remove_misp_ss(input_space_manager, testcase, site)
            return testcase
        else:
            self._add_misp_ss(input_space_manager, testcase, site, type="valid")
            return testcase

    def destroy_mutate(self, testcase, site, **kwargs):
        
        """Perform a destroy mutation on the test case."""
        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")

        if not input_space_manager:
            logger.warning("Input space manager is not provided.")
            return testcase

        if not site:
            logger.warning("No MISP_SS site is provided.")
            return testcase

        if site in testcase.matched_MISP:
            self._remove_misp_ss(input_space_manager, testcase, site)
        else:
            self._add_misp_ss(input_space_manager, testcase, site, type="invalid")

        return testcase

    def _remove_misp_ss(
        self,
        input_space_manager: InputSpaceManager,
        testcase: TestCase,
        misp_ss: MISP_SS,
    ) -> None:
        """Remove the MISP_SS from the test case."""
        testcase.matched_MISP.remove(misp_ss)
        subspace = testcase.matched_Subspace[misp_ss.space_name]

        if subspace is None:
            logger.warning(
                f"No matched Subspace found for MISP_SS '{misp_ss}' can be removed."
            )
            return testcase

        input_space_manager.remove_subspace(testcase, misp_ss, subspace)
        logger.debug(f"Removed MISP_SS site: {misp_ss}")

    def _add_misp_ss(
        self,
        input_space_manager: InputSpaceManager,
        testcase: TestCase,
        misp_ss: MISP_SS,
        type:str
    ) -> None:
        """Add the MISP_SS to the test case."""
        if misp_ss in testcase.matched_MISP:
            logger.warning(f"MISP_SS '{misp_ss}' already exists in the testcase.")
        else:
            subspace_list = misp_ss.get_subspace_list(type)
            if len(subspace_list) > 0:
                testcase.matched_MISP.append(misp_ss)
                subspace = random.choice(misp_ss.get_subspace_list(type))
                logger.debug(f"add new Subspace for MISP mutation: {subspace}")
                input_space_manager.add_subspace(testcase, misp_ss, subspace)
            else:
                logger.warning(
                    f"No matched Subspace found for MISP_SS '{misp_ss}' can be added."
                )
            return testcase

