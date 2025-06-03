from typing import List, Any, Optional
from pydantic import BaseModel, Field

from hirest.model.parameter import Parameter


class Operation(BaseModel):
    """
    Operation class represents a REST API operation. An Operation is identified by a unique operation id (method + url).
    """

    method: str = Field(
        ..., description="The method of the operation, e.g., GET, POST, PUT, DELETE."
    )
    url: str = Field(..., description="The URL of the operation, e.g., /users/{id}.")
    op_name: str = Field(
        None, description="The name of the operation, e.g., GET /users/{id}."
    )
    param_list: List[Parameter] = Field(
        ..., description="The list of parameters of the operation."
    )
    raw_doc_slide: dict[str, Any] = Field(
        ..., description="The raw OpenAPI doc slide of the operation."
    )
    dependencies: List[str] = Field(
        None, description="The multi-parameter dependencies of the operation."
    )

    def __init__(self, **data):
        """
        Custom initialization to automatically generate `op_name` from `method` and `url`.
        """
        super().__init__(**data)
        self.op_name = f"{self.method} {self.url}"

    def get_param_type(self, param_name: str) -> str:
        """
        Get the type of a parameter by its name.
        Args:
            param_name (str): The name of the parameter.
        Returns:
            str: The type of the parameter.
        """
        for param in self.param_list:
            if param.param_name == param_name:
                return param.param_type

        raise ValueError(
            f"Parameter {param_name} not found in operation {self.op_name}."
        )
