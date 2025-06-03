from pydantic import BaseModel, Field
from typing import Optional


class Parameter(BaseModel):
    """
    Parameter class represents a parameter of a REST API operation.
    """

    param_name: str = Field(..., description="The name of the parameter, e.g., 'id'.")
    param_type: str = Field(..., description="The parameter type, e.g., path, query, header, body.")
    val_type: str = Field(..., description="The value type of the parameter, e.g., string, integer, boolean, number.")
    is_required: bool = Field(False, description="Whether the parameter is required. Default is False.")
    description: Optional[str] = Field(None, description="The description of the parameter, e.g., 'The id of the user.'")