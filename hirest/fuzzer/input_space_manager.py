import logging, json, random
from typing import Any

from hirest.model.misp import MISP, MISP_SS, MixedSingleSpace, Subspace
from hirest.model.sisp import SISP, SISP_SS
from hirest.model.testcase import TestCase

logger = logging.getLogger(__name__)


class InputSpaceManager:
    """
    InputSpaceManager Class: responsible for managing the input space (SISP, MISP) of the test cases mutation.
    """

    def __init__(self):
        """
        sisps: dict[str, list[str,SISP]]: key is the operation name, value is a list of SISP objects for each parameter.
        misps: dict[str, MISP]: key is the operation name, value is MISP objects.
        """
        self.sisps: dict[str, dict[str, SISP]] = {}
        self.misps: dict[str, MISP] = {}

    def load_sisps(self, data: list[dict[str, Any]]) -> None:
        """convert the SISP input file data to SISP object.
        Args:
            sisp_data (dict[str, Any]): SISP data (a json list) from the partition file.
        Returns:
            None
        """
        for entry in data:
            sisp = SISP.model_validate(entry)
            op_name = sisp.op_name
            param_name = sisp.param_name
            self.sisps.setdefault(op_name, {})[param_name] = sisp

        for op_name in self.sisps:
            logger.debug(
                f"Loaded SISP for operation '{op_name}': {json.dumps(self.sisps[op_name], default=str, indent=2)}"
            )

    def load_misps(self, misp_data: list[dict[str, Any]]) -> None:
        """convert the MISP input file data to MISP object.
        Args:
            misp_data (list[dict[str, Any]): MISP data from the partition file.
        Returns:
            None
        """

        for misp_entry in misp_data:
            try:
                misp = MISP.parse_obj(misp_entry)
                self.misps[misp.op_name] = misp
            except Exception as e:
                logger.error(f"Failed to load MISP: {misp_entry}, error: {e}")

        for op_name in self.misps:
            logger.debug(
                f"Loaded MISP for operation '{op_name}': {json.dumps(self.misps[op_name], default=str, indent=2)}"
            )

    def get_misp_ss(
        self, op_name: str, selected_spaces: list[str] = []
    ) -> tuple[list[MISP_SS], dict[str, Subspace]]:
        """convert the selected spaces to MISP SS (selected subspace).
        Args:
            selected_spaces (list[str]): list of selected spaces, e.g. ["space1-subspace1", "space2-subspace2"]
        Returns:
            list[MISP_SS]: list of MISP SS (selected subspace) of the selected input space.
        """
        misp_ss_list = []
        subspace_dict = {}

        misp = self.misps[op_name]
        for entry in selected_spaces:
            misp_ss_name, subspace_name = entry.split("-")
            misp_ss = misp.query_misp_ss_by_name(misp_ss_name)
            subspace = misp_ss.query_subspace_by_name(subspace_name)
            misp_ss_list.append(misp_ss)
            subspace_dict[misp_ss.space_name] = subspace
            logger.debug(
                f"Loaded MISP SS for operation '{op_name}': {json.dumps(misp_ss, default=str, indent=2)}"
                f" and subspace '{subspace_name}': {json.dumps(subspace, default=str, indent=2)}"
            )

        return misp_ss_list, subspace_dict

    def get_sisp_ss(
        self, op_name: str, selected_parameters: dict[str, Any]
    ) -> list[SISP_SS]:
        """convert the selected parameters to SISP SS (selected subspace).
        Args:
            selected_parameters (dict[str, Any]): list of selected parameters, e.g. {"parameter1": ..., "parameter2": ...}
        Returns:
            list[SISP_SS]: list of SISP SS (selected subspace) of the selected input space.
        """
        sisp_ss_list = []
        for param_name in selected_parameters:
            sisp_info = selected_parameters[param_name]
            sisp_ss_list.append(
                self.sisps[op_name][param_name].select_ss_by_category(
                    sisp_info["input_space_category"]
                )
            )
        return sisp_ss_list

    def update_subspace(
        self, testcase: TestCase, misp_ss: MISP_SS, removed: Subspace, added: Subspace
    ) -> None:
        """update the subspace of the testcase.
        Args:
            testcase (TestCase): the test case to be updated.
            misp_ss (MISP_SS): the MISP SS to be updated.
            removed (Subspace): the subspace to be removed.
            added (Subspace): the subspace to be added.
        Returns:
            None
        """
        if misp_ss.space_name not in testcase.matched_Subspace:
            logger.warning(
                f"misp_ss {misp_ss.space_name} not found in the matched subspaces of the test case."
            )
            return
        backup_testcase = TestCase.backup(testcase)
        self.remove_subspace(testcase, misp_ss, removed)
        add_success: bool = self.add_subspace(testcase, misp_ss, added)
        if not add_success:
            logger.warning(
                f"Failed to add subspace {added.subspace_name} of MISP_SS {misp_ss.space_name} to the test case after removing subspace {removed.subspace_name}, backup restored."
            )
            testcase.restore(backup_testcase)
            logger.debug(f"Restored test case to backup after failed subspace update: {testcase}")
            return 
        else:
            logger.debug(
                f"Successfully updated subspace from {removed.subspace_name} to {added.subspace_name} for MISP_SS {misp_ss.space_name} in the test case."
            )

    def remove_subspace(
        self, testcase: TestCase, misp_ss: MISP_SS, removed: Subspace
    ) -> None:
        """remove the subspace of the testcase.
        Args:
            testcase (TestCase): the test case to be updated.
            misp_ss (MISP_SS): the MISP SS to be updated.
            removed (Subspace): the subspace to be removed.
        Returns:
            None
        """

        "remove the subspace object from the matched list of testcase."
        if removed != testcase.matched_Subspace.get(misp_ss.space_name):
            logger.warning(
                f"Subspace {removed.subspace_name} of misp_ss {misp_ss.space_name} not found in the matched subspaces of the test case."
            )
            return

        for space_name, subspace in testcase.matched_Subspace.items():
            if subspace == removed:
                del testcase.matched_Subspace[space_name]
                logger.debug(
                    f"Removing subspace {removed.subspace_name} from the matched subspaces of the test case."
                )
                break

        "remove the sisp_ss object for the subspace from the matched sisp_ss list of testcase."

        removed_sisp_ss = list[SISP_SS]()
        for sisp_ss in testcase.matched_SISP:
            mss = subspace.query_mss_by_param(sisp_ss.param_name)
            for entry in mss:
                if entry.input_space_category == sisp_ss.category:
                    removed_sisp_ss.append(sisp_ss)
                    break

        logger.debug(
            f"Removing {len(removed_sisp_ss)} SISP SS {removed_sisp_ss} from the matched SISP SS list of the test case."
        )
        for sisp_ss in removed_sisp_ss:
            self.remove_sisp_ss(testcase, sisp_ss)

        """update the matched SISP SS for the involved parameters after removing the subspace."""
        involved_parameters = misp_ss.involved_parameters
        for parameter in involved_parameters:
            new_sisp_ss = self._update_matched_sisp_ss(testcase, parameter)
            logger.debug(
                f"Updated matched SISP SS {new_sisp_ss} for parameter '{parameter}' after removing subspace '{removed.subspace_name}' of MISP_SS '{misp_ss.space_name}'"
            )

    def add_subspace(
        self, testcase: TestCase, misp_ss: MISP_SS, added: Subspace
    ) -> bool:
        """add the subspace of the testcase.
        Args:
            testcase (TestCase): the test case to be updated.
            misp_ss (MISP_SS): the MISP SS to be updated.
            added (Subspace): the subspace to be added.
        Returns:
            None
        """
        
        "add the subspace object to the matched list of testcase."
        if added in testcase.matched_Subspace.values():
            logger.warning(
                f"Subspace {added.subspace_name} of MISP_SS {misp_ss.space_name} already exists in the matched subspaces of the test case."
            )
            return False
        
        testcase.matched_Subspace[misp_ss.space_name] = added
        involved_parameters = misp_ss.involved_parameters

        for parameter in involved_parameters:
            new_sisp_ss = self._update_matched_sisp_ss(testcase, parameter)
            if new_sisp_ss is None:
                logger.warning(
                    f"Failed to update matched SISP SS for parameter '{parameter}' after adding subspace '{added.subspace_name}' of MISP_SS '{misp_ss.space_name}'."
                )
                return False

        return True

        # for parameter in added.parameter:
        #     mss = added.query_mss_by_param(parameter)

        #     selected_mss = random.choice(mss)
        #     testcase.matched_SISP.append(
        #         self.sisps[testcase.operation.op_name]
        #         .get(parameter)
        #         .select_ss_by_category(selected_mss.input_space_category)
        #     )

    def _resolve_effective_sisp_ss(self, testcase: TestCase, parameter: str) -> list[SISP_SS]:
        """Resolve the effective SISP SS for a given parameter.
        Args:
            testcase (TestCase): The test case.
            parameter (str): The parameter name.
        Returns:
            list[SISP_SS]: The list of effective SISP SS.
        """
        mss_list_set: list[list[MixedSingleSpace]] = []
        for subspace in testcase.matched_Subspace.values():
            mss_list = subspace.query_mss_by_param(parameter)
            if mss_list and len(mss_list) > 0:
                mss_list_set.append(mss_list)
        
        if len(mss_list_set) == 0:
            logger.warning(
                f"No effective SISP SS found for parameter '{parameter}' because no matched subspace contains the parameter."
            )
            return []

        """
        resolve the effective SISP SS by intersecting the MSS lists.
        """
        base_mss_list = mss_list_set[0]
        for mss_list in mss_list_set[1:]:
            for mss in base_mss_list:
                if mss.input_space_category not in [item.input_space_category for item in mss_list]:
                    base_mss_list.remove(mss)
        
        logger.debug(f"intersected MSS list for parameter '{parameter}': {base_mss_list}")
        
        'convert the effective MSS list to SISP SS list.'
        effective_sisp_ss_list:list[SISP_SS] = []
        for mss in base_mss_list:
            sisp_ss = self.sisps[testcase.operation.op_name][parameter].select_ss_by_category(mss.input_space_category)
            effective_sisp_ss_list.append(sisp_ss)
            
        logger.debug(f"Effective SISP SS list for parameter '{parameter}': {effective_sisp_ss_list}")
        return effective_sisp_ss_list if len(effective_sisp_ss_list) > 0 else []
    
    def _update_matched_sisp_ss(self, testcase: TestCase, parameter: str) -> MISP_SS | None:
        """Update the matched SISP SS for a given parameter after the subspace update.
        Args:
            testcase (TestCase): The test case.
            parameter (str): The parameter name.
        Returns:
            MISP_SS | None: The updated SISP SS or None if not found.
        """
        effective_sisp_ss = self._resolve_effective_sisp_ss(testcase, parameter)
        if not effective_sisp_ss or len(effective_sisp_ss) == 0:
            logger.warning(
                f"No effective SISP SS found for parameter '{parameter}' after subspace update."
            )
            return None
        else:
            logger.debug(
                f"Effective SISP SS for parameter '{parameter}' after subspace update: {effective_sisp_ss}"
            )
            selected_sisp_ss = random.choice(effective_sisp_ss)
            logger.debug(
                f"Selected SISP SS for parameter '{parameter}' after subspace update: {selected_sisp_ss}"
            )
            testcase.matched_SISP = [
                sisp_ss for sisp_ss in testcase.matched_SISP if sisp_ss.param_name != parameter
            ] + [selected_sisp_ss]

            return selected_sisp_ss

    def remove_sisp_ss(self, testcase: TestCase, removed: SISP_SS) -> None:
        """remove the SISP SS of the testcase.
        Args:
            testcase (TestCase): the test case to be updated.
            removed (SISP_SS): the SISP SS to be removed.
        Returns:
            None
        """
        if removed in testcase.matched_SISP:
            testcase.matched_SISP.remove(removed)

    def query_invalid_sisp_ss_by_param_name(self, testcase: TestCase, parameter: str) -> list[SISP_SS]:
        """get the invalid SISP SS for a given parameter.
        Args:
            testcase (TestCase): The test case.
            parameter (str): The parameter name.
        """

        invalid_sisp_ss_list = []
        for sisp_ss in self.sisps[testcase.operation.op_name][parameter].invalid:
            if sisp_ss not in testcase.matched_SISP:
                invalid_sisp_ss_list.append(sisp_ss)

        logger.debug(
            f"Queried {len(invalid_sisp_ss_list)} invalid SISP SS for parameter '{parameter}': {invalid_sisp_ss_list}"
        )
        return invalid_sisp_ss_list