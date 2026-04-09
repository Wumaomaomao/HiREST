from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class MixedSingleSpace(BaseModel):
    tag: str = Field(..., description="The single parameter space is valid or invalid.")
    type: Optional[str] = Field(
        None, description="The type of parameter value in single parameter space."
    )
    format: Optional[str] = Field(
        None, description="The format of parameter value in single parameter space."
    )
    input_space_category: str = Field(..., description="The input space category.")
    description: str = Field(
        ..., description="The description of parameter value in single parameter space."
    )
    representative_samples: List[Any] = Field(
        ..., description="The representative samples of parameter space."
    )


class Subspace(BaseModel):
    subspace_name: str = Field(
        ...,
        description="Name of subspace, e.g. subspace1, subspace2, error_space1, error_space2",
    )
    single_parameter_spaces: Dict[str, List[MixedSingleSpace]] = Field(
        ..., description="single parameter spaces of subspace."
    )
    parameter: List[str] = Field(
        ..., description="The must be existed parameter of subspace."
    )
    parameter_value: List[str] = Field(
        ..., description="The relationship between parameter and value of subspace."
    )
    parameter_parameter: List[str] = Field(
        ..., description="The relationship between parameter and parameter of subspace."
    )

    def query_mss_by_param(self, param_name: str) -> List[MixedSingleSpace]:
        """select the mixed single space by parameter name.
        Args:
            param_name (str): the name of the parameter. e.g. id, name
        Returns:
            List[MixedSingleSpace]: the mixed single space with the specified parameter name.
        """

        if param_name in self.single_parameter_spaces.keys():
            return self.single_parameter_spaces[param_name]

        return []


class MISP_SS(BaseModel):
    space_name: str = Field(
        ..., description="The name of the space. e.g. space1, space2"
    )
    satisfied_dependencies: str = Field(
        ..., description="The satisfied dependencies of the space."
    )
    involved_parameters: List[str] = Field(
        ..., description="The parameters involved in the space."
    )
    subspace_list: List[Subspace] = Field(
        ..., description="The subspaces and error_spaces of the space."
    )

    def get_subspace_list(self, tag="valid") -> List[Subspace]:
        """get the subspace list by tag.
        Args:
            tag (str): the tag of the subspace, e.g. valid, invalid
        Returns:
            List[Subspace]: the subspace list with the specified tag.
        """

        if tag != "valid" and tag != "invalid":
            raise ValueError(f"Invalid tag: {tag}. Must be 'valid' or 'invalid'.")

        subspace_list = []
        if tag == "valid":
            for entry in self.subspace_list:
                if entry.subspace_name.startswith("subspace"):
                    subspace_list.append(entry)
        elif tag == "invalid":
            for entry in self.subspace_list:
                if entry.subspace_name.startswith("error_space"):
                    subspace_list.append(entry)

        return subspace_list

    def query_subspace_by_name(self, subspace_name: str) -> Subspace:
        """select the subspace by name.
        Args:
            subspace_name (str): the name of the subspace. e.g. subspace1, error_space1
        Returns:
            Subspace: the subspace with the specified name.
        """

        for entry in self.subspace_list:
            if entry.subspace_name == subspace_name:
                return entry

        raise ValueError(
            f"Invalid name of subspace {subspace_name} of space {self.space_name}"
        )


class MISP(BaseModel):
    op_name: str = Field(..., description="The name of the operation")
    space_list: List[MISP_SS] = Field(..., description="The list of MISP_SSs.")

    def query_misp_ss_by_name(self, ss_name: str) -> MISP_SS:
        """select the subspace by name.
        Args:
            ss_name (str): the name of the MISP ss. e.g. space1, space2
        Returns:
            MISP_SS: the MISP SS with the specified name.
        """

        for entry in self.space_list:
            if entry.space_name == ss_name:
                return entry

        raise ValueError(
            f"Invalid name of MISP SS {ss_name} of operation {self.op_name}"
        )
