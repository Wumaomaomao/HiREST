import random

from typing import List, Any
from pydantic import BaseModel, Field


class SISP_SS(BaseModel):
    """
    SISP_SS : Single Parameter Input Space Partition Subspace in cosrest
    """

    param_name: str = Field(..., description="The name of the parameter, e.g., 'id'.")
    category: str = Field(
        ...,
        description="The category of the subspace, e.g., 'positive_integer', 'negative_integer', 'zero'.",
    )
    description: str = Field(
        ..., description="The description of the subspace, e.g., 'positive integers'."
    )
    samples: List[Any] = Field(
        ..., description="The value samples of the subspace, e.g., ['1', '2', '3']."
    )

    def generate_val(self) -> Any:
        """generate a sample value from the SISP SS.
        Returns:
            Any: the generated sample value.
        """
        return random.choice(self.samples)


class SISP(BaseModel):
    """
    SISP : Single Parameter Input Space Partition in cosrest
    """

    op_name: str = Field(
        ..., description="The name of the operation, e.g., 'GET /users/{id}'."
    )
    type: str = Field(..., description="The type of the parameter, e.g., 'string', 'integer'.")
    param_name: str = Field(..., description="The name of the parameter, e.g., 'id'.")
    format: List[str] = Field(
        ..., description="The format of the parameter, e.g., ['[0-9]+', '[a-zA-Z]+']."
    )
    valid: List[SISP_SS] = Field(
        [],
        description="The valid subspace of the parameter, e.g., [SISP_SS1, SISP_SS2].",
    )
    invalid: List[SISP_SS] = Field(
        [],
        description="The error subspace of the parameter, e.g., [SISP_SS1, SISP_SS2].",
    )

    def select_ss_by_category(self, category: str) -> SISP_SS:
        """select the SISP SS by category.
        Args:
            category (str): the category of the SISP SS, e.g., 'positive_integer', 'negative_integer', 'zero'.
        Returns:
            SISP_SS: the SISP SS with the specified category.
        """
        for entry in self.valid:
            if entry.category == category:
                return entry
        for entry in self.invalid:
            if entry.category == category:
                return entry

        raise ValueError(
            f"Invalid category of parameter {self.param_name} of operation {self.op_name}: {category}, SISP: {self}"
        )

    def parse_sisp_ss(self, param_name: str, data: dict[str, Any]) -> None:
        """load the SISP SS (selected subspace) from the input data.
        Args:
            data (dict[str, Any]): SISP SS data from the input file.
        Returns:
            None
        """
        if data["valid_input_space_categories"] is not None:
            for entry in data["valid_input_space_categories"]:
                self.valid.append(
                    SISP_SS(
                        param_name=param_name,
                        category=entry["input_space_category"],
                        description=entry["description"],
                        samples=entry["representative_samples"],
                    )
                )

        if data["invalid_input_space_categories"] is not None:
            for entry in data["invalid_input_space_categories"]:
                self.invalid.append(
                    SISP_SS(
                        param_name=param_name,
                        category=entry["input_space_category"],
                        description=entry["description"],
                        samples=entry["representative_samples"],
                    )
                )
