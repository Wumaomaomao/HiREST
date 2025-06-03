import logging, re

from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field
from urllib.parse import urljoin

from hirest.model.operation import Operation

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """
    ContentType: Enum for HTTP content types.
    """

    ANY = "*/*"
    JSON = "application/json"
    TEXT = "text/plain"
    JSON_UTF8 = "application/json;charset=utf-8"
    FORM_URLENCODED = "application/x-www-form-urlencoded"
    

    @classmethod
    def parse_content_type(cls, request_body: dict) -> "ContentType":
        """Parse the content type from request_body description."""
        content = request_body.get("content", {})
        logger.debug(f"content types: {list(content.keys())}")
        for type in content.keys():
            if type == "application/json":
                return cls.JSON
            # elif re.search(r"\+json(\s*;|$)", type):
            #     return cls.JSON
            elif type == "text/plain":
                return cls.TEXT
            elif type == "application/json;charset=UTF-8":
                return cls.JSON_UTF8
            elif type == "application/x-www-form-urlencoded":
                return cls.FORM_URLENCODED
        
        return cls.ANY

class SchemaType(str, Enum):
    """
    SchemaType: Enum for schema types.
    """

    OBJECT = "object"
    ARRAY = "array"
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"


    @classmethod
    def parse_schema_type(cls, schema: dict) -> "SchemaType":
        """Parse the schema type from schema description."""
        return cls(schema.get("type"))

class Request(BaseModel):
    """
    Request: Represents a rendered HTTP request.
    """

    base_url: str = Field(
        ..., description="The base URL of the request, e.g., http://example.com."
    )
    method: str = Field(
        ..., description="The method of the request, e.g., GET, POST, PUT, DELETE."
    )
    path: str = Field(..., description="The path of the request, e.g., /users/1.")
    rendered_url: str = Field(
        None,
        description="The full URL of the request, e.g., http://example.com/users/1.",
    )
    content_type: ContentType = Field(
        ContentType.ANY,
        description="The content type of the request, e.g., application/json.",
    )
    headers: Dict[str, str] = Field(
        {},
        description="The headers of the request, e.g., {'Content-Type': 'application/json'}.",
    )
    body: Dict[str, Any] = Field(
        {}, description="The body of the request, e.g., {'name': 'Alice'}."
    )
    path_params: Dict[str, Any] = Field(
        {}, description="The path parameters of the request, e.g., {'id': '1'}."
    )
    query_params: Dict[str, Any] = Field(
        {}, description="The query parameters of the request, e.g., {'name': 'Alice'}."
    )
    body_params: Dict[str, Any] = Field(
        {}, description="The body parameters of the request, e.g., {'name': 'Alice'}."
    )

    def generate_request(
        self, operation: Operation, param_vals: Dict[str, Any]
    ) -> None:
        """Generate the request based on the operation and parameter values.
        Args:
            operation (Operation): The operation template of the request.
            param_vals (Dict[str, Any]): The parameter values of the request.
        """
        self._bucket_param_vals_by_type(operation, param_vals)
        self.build_url()
        self.build_body(operation.raw_doc_slide)
        self.build_headers()

        logger.debug(
            f"generate request: method: {self.method}, url: {self.rendered_url}, headers: {self.headers}, request body: {self.body}"
        )

    def build_url(self) -> str:
        """Build the full URL from the base URL, path, and query parameters.
        Returns:
            str: The full URL of the request.
        """
        resolved = self._resolve_path_params(self.path)
        full_url = urljoin(self.base_url, resolved.lstrip("/"))
        self.rendered_url = self._resolve_query_params(full_url)

        logger.debug(f"build request url: {self.rendered_url}")

        return self.rendered_url

    def build_headers(self) -> Dict[str, str]:
        """Build the headers of the request.
        Returns:
            Dict[str, str]: The headers of the request.
        """
        if self.content_type:
            self.headers["Content-Type"] = self.content_type

        logger.debug(f"build request headers: {self.headers}")

        return self.headers

    def build_body(self, openapi_slide: Dict) -> Dict[str, Any]:
        """Build the body of the request.
        Args:
            schema (Dict): The schema of the request body.
        Returns:
            Dict[str, Any]: The body of the request.
        """
        if "requestBody" in openapi_slide:
            self.content_type = ContentType.parse_content_type(
                openapi_slide["requestBody"]
            )
            match self.content_type:
                case ContentType.ANY:
                    logger.debug(
                        f"request body content type is not specified, using default: {self.content_type}, skipping body generation"
                    )
                case ContentType.TEXT:
                    logger.debug(
                        f"request body content type is text, using content type: {self.content_type}"
                    )
                    #TODO: need to support text body further
                    self.body = "plain text"
                    
                case ContentType.JSON:
                    logger.debug(
                        f"request body content type is json, using content type: {self.content_type}"
                    )
                    self.body = self._resolve_json_body(
                    openapi_slide["requestBody"]["content"]
                    ["application/json"]["schema"])

                    logger.debug(f"build json request body: {self.body}")
                
                case ContentType.JSON_UTF8:
                    logger.debug(
                        f"request body content type is json-utf8, using content type: {self.content_type}"
                    )
                    self.body = self._resolve_json_body(
                    openapi_slide["requestBody"]["content"]
                    ["application/json;charset=UTF-8"]["schema"])

                    logger.debug(f"build json-UTF8 request body: {self.body}")

                case ContentType.FORM_URLENCODED:
                    logger.debug(
                        f"request body content type is form-urlencoded, using content type: {self.content_type}"
                    )
                    self.body = self._resolve_form_urlencoded_body(
                        openapi_slide["requestBody"]["content"][
                            "application/x-www-form-urlencoded"
                        ]["schema"]
                    )
                    logger.debug(f"build form urlencoded request body: {self.body}")

        return self.body

    def _resolve_path_params(self, path: str) -> str:
        """Resolve the path parameters in the request path."""
        resolved_path = self.path
        for key, value in self.path_params.items():
            resolved_path = resolved_path.replace(f"{{{key}}}", str(value))

        return resolved_path

    def _resolve_query_params(self, path: str) -> str:
        """Resolve the query parameters in the request path."""
        resolved_path = path
        if self.query_params and len(self.query_params) > 0:
            query_string = "&".join(
                f"{key}={value}" for key, value in self.query_params.items()
            )
            resolved_path += "?" + query_string
        return resolved_path

    def _resolve_form_urlencoded_body(
        self, schema: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Build the form-urlencoded body of the request.
        Returns:
            Dict[str, Any]: The form-urlencoded body of the request.
        """
        body = {}
        for param_name, attrs in schema["properties"].items():
            if param_name in self.body_params:
                param_value = self.body_params[param_name]
                body[param_name] = str(param_value)
            else:
                logger.debug(f"skip the parameter {param_name} in the request body")

        return body

    def _resolve_json_body(self, schema: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Build the JSON body of the request.
        Returns:
            Dict[str, Any]: The JSON body of the request.
        """
        body = {}

        match SchemaType.parse_schema_type(schema):
            case SchemaType.OBJECT:
                logger.debug("request body type is json object")
                body:dict = self._object_body_builder("", schema["properties"])
            case SchemaType.ARRAY:
                logger.debug("request body type is json array")
                body:list = self._array_body_builder("", schema["items"])
            case _:
                raise ValueError(f"Unknown schema type for json requestBody: {schema['type']}")
        
        return body
    
    def _object_body_builder(
        self, prefix:str ,properties: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Build the object body of the requestBody."""
        body = {}
        for param_name, attrs in properties.items():
            obj_prefix = f"{prefix}.{param_name}" if prefix else param_name
            logger.debug(f"building object body for {obj_prefix}")
            match SchemaType.parse_schema_type(attrs):
                case SchemaType.OBJECT:
                    body[param_name] = self._object_body_builder(obj_prefix, attrs["properties"])
                case SchemaType.ARRAY:
                    body[param_name] = self._array_body_builder(obj_prefix, attrs["items"])
                case _ :
                    full_param_name = obj_prefix
                    if full_param_name in self.body_params:
                        param_value = self.body_params[full_param_name]
                        body[param_name] = str(param_value)
                    else:
                        logger.debug(f"skip the parameter {full_param_name} in the request body")
        return body
    
    def _array_body_builder(
        self, prefix:str, items: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Build the array body of the requestBody."""
        #TODO: default generate the array body with len 1, need to support multiple items in the future
        body = []
        array_prefix = f"{prefix}[]"
        logger.debug(f"building array body for {array_prefix}, type: {SchemaType.parse_schema_type(items)}")
        match SchemaType.parse_schema_type(items):
            case SchemaType.OBJECT:
                body.append(self._object_body_builder(array_prefix, items["properties"]))
            case SchemaType.ARRAY:
                body.append(self._array_body_builder(array_prefix, items["items"]))
            case _:
                full_param_name = array_prefix
                if full_param_name in self.body_params:
                    param_value = self.body_params[full_param_name]
                    body.append(str(param_value))
                else:
                    logger.debug(f"skip the parameter {full_param_name} in the request body")
        
        return body
            
    def _bucket_param_vals_by_type(
        self, operation: Operation, param_vals: Dict[str, Any]
    ) -> None:
        """Bucket the parameter values by type."""
        for param in param_vals.keys():
            param_type = operation.get_param_type(param)
            if param_type == "path":
                self.path_params[param] = param_vals[param]
            elif param_type == "query":
                self.query_params[param] = param_vals[param]
            elif param_type == "body":
                self.body_params[param] = param_vals[param]
            else:
                raise ValueError(f"Unknown parameter type : {param_type} for {param}")
