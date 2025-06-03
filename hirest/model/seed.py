from typing import Dict, List

from pydantic import BaseModel, Field

from hirest.model.misp import MixedSingleSpace


class SeedModel(BaseModel):
    op_name : str = Field(..., description="The name of the operation of the seeds.")
    tag : str = Field(..., description="The tag of the seed,  e.g. valid, error")
    selected_spaces : List[str] = Field(..., description="The spaces selected by the seed.")
    selected_parameters_list : Dict[str, MixedSingleSpace] = Field(..., description="The parameters' single space of the selected spaces.")
    parameter_parameter : List[str] = Field(..., description="The relationship between parameter and parameter .")
