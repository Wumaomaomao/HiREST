from enum import Enum
import logging

from typing import List, Any, Optional
from pydantic import BaseModel, Field

from hirest.model.operation import Operation
from hirest.model.misp import MISP_SS, MixedSingleSpace, Subspace
from hirest.model.sisp import SISP_SS
from hirest.model.request import Request

logger = logging.getLogger(__name__)

class MutationType(str, Enum):
    """
    MutationType: Enum for mutation types, this value is \
      assigned to the test case by casemanager pop next testcase.

    
    NORMAL: Normal mutation, only contains valid (normal)input spaces. \n
    DESTROY: Destroy mutation, only contains invalid (error) input spaces.
    """

    NORMAL = "normal"
    DESTROY = "destroy"



class TestCase(BaseModel):
    """
    TestCase class: Stores information about a test case, including operation template, matched spaces, request, response, etc.
    """

    operation: Operation = Field(
        ..., description="The operation template of the test case."
    )
    matched_MISP: Optional[List[MISP_SS]] = Field(
        None, description="The matched MISP spaces of the test case."
    )
    matched_Subspace: Optional[dict[str, Subspace]] = Field(
        None,
        description="The matched subspaces of the test case, this is a dict[MISP_NAME, Subspace], because one MISP may have multiple subspaces, but they are un.",
    )
    matched_SISP: Optional[List[SISP_SS]] = Field(
        None, description="The matched SISP spaces of the test case."
    )
    param_vals: Optional[dict[str, Any]] = Field(
        {},
        description="The parameter values of the test case, e.g., [{'id': 1}, {'name': 'Alice'}].",
    )
    request: Optional[Request] = Field(
        None, description="The request of the test case."
    )
    response: Optional[dict[str, Any]] = Field(
        None,
        description="The response of the test case, e.g., {'status': 200, 'body': {'id': 1, 'name': 'Alice'}}.",
    )

    mutation_type: MutationType = Field(
        MutationType.NORMAL,
        description="TFhe mutation type of the test case, used to distinguish between normal and destroy mutations.",
    )
    
    def __eq__(self, other: object) -> bool:
        """Check if two test cases are equal based on their operation and matched spaces."""
        if not isinstance(other, TestCase):
            return False

        if self.operation != other.operation:
            return False

        if bool(self.matched_MISP) != bool(other.matched_MISP):
            return False
        if self.matched_MISP:
            if len(self.matched_MISP) != len(other.matched_MISP):
                return False
            if not all(x in other.matched_MISP for x in self.matched_MISP):
                return False

        if self.matched_Subspace != other.matched_Subspace:
            return False
        
        if bool(self.matched_SISP) != bool(other.matched_SISP):
            return False
        if self.matched_SISP:
            if len(self.matched_SISP) != len(other.matched_SISP):
                return False
            if not all(x in other.matched_SISP for x in self.matched_SISP):
                return False

        return True

    @classmethod
    def derive(cls, testcase: "TestCase") -> "TestCase":
        """Create a new test case based on the operation template with empty request content."""
        return cls(
            operation=testcase.operation,
            matched_MISP=testcase.matched_MISP.copy() if testcase.matched_MISP else None,
            matched_Subspace=testcase.matched_Subspace.copy() if testcase.matched_Subspace else None,
            matched_SISP=testcase.matched_SISP.copy() if testcase.matched_SISP else None,
        )
    
    @classmethod
    def backup(cls, testcase: "TestCase") -> "TestCase":
        """Create a backup of the test case, this is used for mutation, because the mutation may fail, we need to backup the original test case."""
        return cls(
            operation=testcase.operation,
            matched_MISP=testcase.matched_MISP.copy() if testcase.matched_MISP else None,
            matched_Subspace=testcase.matched_Subspace.copy() if testcase.matched_Subspace else None,
            matched_SISP=testcase.matched_SISP.copy() if testcase.matched_SISP else None,
            param_vals=testcase.param_vals.copy() if testcase.param_vals else None,
            request=testcase.request.copy() if testcase.request else None,
            response=testcase.response.copy() if testcase.response else None,
            mutation_type=testcase.mutation_type,
        )
    
    def restore(self, backup: "TestCase") -> None:
        """Restore the test case from the backup, this is used for mutation, because the mutation may fail, we need to restore the original test case."""
        self.operation = backup.operation
        self.matched_MISP = backup.matched_MISP.copy() if backup.matched_MISP else None
        self.matched_Subspace = backup.matched_Subspace.copy() if backup.matched_Subspace else None
        self.matched_SISP = backup.matched_SISP.copy() if backup.matched_SISP else None
        self.param_vals = backup.param_vals.copy() if backup.param_vals else None
        self.request = backup.request.copy() if backup.request else None
        self.response = backup.response.copy() if backup.response else None
        self.mutation_type = backup.mutation_type if backup.mutation_type else None

    def generate_param_vals(self) -> None:
        """Generate parameter values for the test case based on the matched SISP spaces."""
        try:
            for sisp_ss in self.matched_SISP:
                val = sisp_ss.generate_val()
                self._set_param_val(sisp_ss.param_name, val)
        except Exception as e:
            logger.error(
                f"Failed to generate parameter values for test case: {self.operation.op_name}, error: {e}"
            )

    def generate_request(self, op_base_url:str) -> None:
        """Initialize the request for the test case based on the operation template."""
        try:
            self.request = Request(
                base_url=op_base_url,
                path=self.operation.url,
                method=self.operation.method,
                params=self.param_vals,
            )
            self.request.generate_request(self.operation, self.param_vals)

        except Exception as e:
            logger.error(
                f"Failed to initialize request for test case: {self.operation.op_name}, error: {e}",
                exc_info=True,
            )

    def query_mixed_subspace_by_param(
        self, param_name: str, tag: str = "valid"
    ) -> List[MixedSingleSpace]:
        """Query the mixed single space list by parameter name.
        Args:
            param_name (str): The name of the parameter.
            tag (str): The tag of the mixed single space, ['valid', 'invalid'].
        Returns:
            List[MixedSingleSpace]: The mixed single space with the specified parameter name.
        """
        if self.matched_Subspace is None:
            return []

        if tag != "valid" and tag != "invalid":
            raise ValueError(f"Invalid tag: {tag}. Must be 'valid' or 'invalid'.")

        mss_list = list[MixedSingleSpace]()
        for entry in self.matched_Subspace.values():
            mss_list.extend(entry.query_mss_by_param(param_name))

        taged_mss_list = []
        for entry in mss_list:
            if entry.tag == tag:
                taged_mss_list.append(entry)
        return taged_mss_list

    def query_mispss_by_subspace(self, subspace: Subspace) -> MISP_SS:
        """Query the MISP SS by subspace.
        Args:
            subspace (Subspace): The subspace to be queried.
        Returns:
            MISP_SS: The MISP SS with the specified subspace.
        """
        if self.matched_MISP is None:
            return None

        for entry in self.matched_MISP:
            if subspace in entry.subspace_list:
                return entry

        raise ValueError(
            f"Invalid subspace {subspace.subspace_name} of operation {self.operation.op_name}, no matched MISP SS found."
        )

    def _set_param_val(self, param_name: str, val: Any) -> None:
        """Set the value of a parameter in the test case.
        Args:
            param_name (str): The name of the parameter.
            val (Any): The value to be set.
        """
        if val == "<MISS_KEY>":
            logger.debug(f'Set the parameter: {param_name} to "<MISS_KEY>", which indicates the parameter key is missing in the request.')
            self.param_vals.pop(param_name, None)
        else:
            self.param_vals[param_name] = val

    
    def query_mss_by_param(self, param_name: str) -> List[MixedSingleSpace]:
        """Query the mixed single space list by parameter name.
        Args:
            param_name (str): The name of the parameter.
        Returns:
            List[MixedSingleSpace]: The mixed single space with the specified parameter name.
        """
        if self.matched_Subspace is None:
            return []

        mss_list = list[MixedSingleSpace]()
        for entry in self.matched_Subspace.values():
            mss_list.extend(entry.query_mss_by_param(param_name))

        return mss_list


class TestCasePool(BaseModel):
    """
    TestCasePool class: Stores the test cases of an operation.
    """

    operation: Operation = Field(
        ..., description="The operation of the test case pool."
    )
    max_size: int = Field(..., description="The maximum size of the test case pool.")
    testcases: Optional[List[TestCase]] = Field(
        [], description="The stored test cases of the test case pool."
    )

    def add_testcase(self, testcase: TestCase) -> None:
        """Add a test case to the pool.
        Args:
            testcase (TestCase): The test case to be added.
        """
        if len(self.testcases) < self.max_size:
            self.testcases.append(testcase)
        else:
            raise ValueError(f"Test case pool is full. Max size: {self.max_size}")
