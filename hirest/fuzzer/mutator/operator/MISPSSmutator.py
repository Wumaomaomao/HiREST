import logging, random

from hirest.model.misp import MISP_SS, Subspace
from hirest.model.testcase import TestCase

from hirest.fuzzer.input_space_manager import InputSpaceManager
from hirest.fuzzer.mutator.operator.mutator import Mutator

logger = logging.getLogger(__name__)


class MISPSSMutator(Mutator):
    """MISPSSmutator class: mutate the Test Case by mutating MISP_SS for an operation.
    select another Subspace for MISP_SS of the operation.
    """
    

    def select_site(self, testcase: TestCase) -> Subspace | None:
        """Select a mutation site for mutation in the test case."""
        # Select a MISP_SS from the matched MISP spaces
        if testcase.matched_Subspace:
            mispss_name, subspace = random.choice(
                list(testcase.matched_Subspace.items())
            )
            return subspace
    
    def valid_mutate(self, testcase: TestCase, **kwargs) -> TestCase:
        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        site = kwargs.get("site")
        # Validate the arguments for mutation
        if not self._validate_args(
            testcase,
            input_space_manager=input_space_manager,
            site=site,
        ):
            logger.warning("Invalid arguments for MISP_SS mutation, terminating mutation.")
            return testcase
        
        logger.debug(f"Validated arguments for MISP_SS mutation site: {site}")

        misp_ss, new_subspace = self._select_new_subspace(
            input_space_manager=input_space_manager,
            testcase=testcase,
            subspace=site,
            type="valid",
        )
        if new_subspace == None:
            return testcase
            
        logger.debug(f"Selected new Subspace for MISP_SS mutation: {new_subspace}")

        testcase = self._update_subspace(
            input_space_manager=input_space_manager,
            testcase=testcase,
            misp_ss=misp_ss,
            subspace=site,
            new_subspace=new_subspace,
        )

        return testcase

    def destroy_mutate(self, testcase: TestCase, **kwargs) -> TestCase:
        """Perform a destroy mutation on the test case."""
        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        site = kwargs.get("site")

        # Validate the arguments for mutation
        if not self._validate_args(
            testcase,
            input_space_manager=input_space_manager,
            site=site,
        ):
            logger.warning("Invalid arguments for MISP_SS mutation, terminating mutation.")
            return testcase

        logger.debug(f"Validated arguments for MISP_SS mutation site: {site}")

        misp_ss, new_subspace = self._select_new_subspace(
            input_space_manager=input_space_manager,
            testcase=testcase,
            subspace=site,
            type="invalid",
        )

        if new_subspace == None:
            return testcase

        logger.debug(f"Selected new Subspace for MISP_SS mutation: {new_subspace}")

        testcase = self._update_subspace(
            input_space_manager=input_space_manager,
            testcase=testcase,
            misp_ss=misp_ss,
            subspace=site,
            new_subspace=new_subspace,
        )

        return testcase

    def _validate_args(self, testcase: TestCase, **kwargs) -> bool:
        """Validate the arguments for mutation."""
        input_space_manager: InputSpaceManager = kwargs.get("input_space_manager")
        site = kwargs.get("site")

        if not input_space_manager:
            logger.warning("Input space manager is not provided.")
            return False

        if not testcase.matched_Subspace:
            logger.warning(
                "No matched Subspace spaces of MISP_SS matched is found in the test case."
            )
            return False

        if not site:
            logger.warning("No site is provided for mutation.")
            return False

        if site not in testcase.matched_Subspace.values():
            logger.warning(
                f"The selected site {site} is not in the matched Subspace spaces."
            )
            return False

        return True

    def _select_new_subspace(
        self,
        input_space_manager: InputSpaceManager,
        testcase: TestCase,
        subspace: Subspace,
        type: str,
    ) -> tuple[MISP_SS, Subspace]:
        """Select a new Subspace for mutation."""

        if type not in ["valid", "invalid"]:
            logger.warning(
                f"Invalid type '{type}' for MISP_SS mutation. Expected 'valid' or 'invalid'."
            )
            return None, None

        op_name = testcase.operation.op_name

        misp_ss = testcase.query_mispss_by_subspace(subspace)
        subspace_list = misp_ss.get_subspace_list(type)

        if not subspace_list:
            logger.warning(
                f"No {type} Subspace found for operation '{op_name}' and subspace '{subspace.subspace_name}'."
            )
            return misp_ss, None

        selectable_subspaces = [
            item
            for item in subspace_list
            if item.subspace_name != subspace.subspace_name
        ]

        if len(selectable_subspaces) == 0:
            logger.warning(
                f"No selectable Subspace found for operation '{op_name}' and subspace '{subspace.subspace_name}'."
            )
            return None, None

        new_subspace = random.choice(selectable_subspaces)

        logger.debug(f"Selected new Subspace for MISP_SS mutation: {new_subspace}")

        return misp_ss, new_subspace

    def _update_subspace(
        self,
        input_space_manager: InputSpaceManager,
        testcase: TestCase,
        misp_ss: MISP_SS,
        subspace: Subspace,
        new_subspace: Subspace,
    )->TestCase:
        """Update the subspace for the MISP_SS in the test case."""
        input_space_manager.update_subspace(testcase, misp_ss, subspace, new_subspace)
        return testcase