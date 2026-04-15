import logging, json
from typing import Any

from hirest.model.request import Request

logger = logging.getLogger(__name__)

class ResourcePool:
    """
    A class to manage a pool of dynamic resources for testing.
    """

    def __init__(self):
        self.pool:dict[str, list[Any]] = {}

    def extract_dynres(self, request: Request, response:dict[str,Any]) -> None:
        """
        Extracts dynamic resources from the response JSON and stores them in the pool.
        """

        if not response or 'text' not in response or not response['text']:
            return 
        
        if not (response['status_code'] >= 200 and response['status_code'] < 300):
            return  
        
        if request.query_params:
            self.extract_succ_param_vals(request.query_params)
        if request.body_params:
            self.extract_succ_param_vals(request.body_params)
        if request.path_params:
            self.extract_succ_param_vals(request.path_params)

        response_json = response['text']
        if isinstance(response_json, str):
            try:
                response_json = json.loads(response_json)
            except json.JSONDecodeError:
                logger.warning("Failed to decode JSON response.")
                return

        if isinstance(response_json, list):
            for item in response_json:
                if isinstance(item, dict):
                    self._extract_item(item)
        elif isinstance(response_json, dict):
            self._extract_item(response_json)
        
        logger.debug(f"extracted dynamic resources: {self.pool}")

    def extract_succ_param_vals(self, param_vals:dict[str,Any]) -> None:
        """
        Extracts dynamic resources from the successful request parameters and stores them in the pool.
        """
        for key, value in param_vals.items():
            self._add_request_dynres_with_branches(key, value)

    def _add_request_dynres_with_branches(self, key: str, value: Any) -> None:
        """Add request parameter value by full key, branch keys and short key aliases."""
        normalized = key[:-2] if key.endswith("[]") else key
        parts = normalized.split(".") if normalized else []

        if not parts:
            return

        # full path + branch paths: a.b.c -> a.b.c, a.b, a
        for i in range(len(parts), 0, -1):
            branch_key = ".".join(parts[:i])
            self._add_dynres(branch_key, value)

        # leaf alias: a.b.c -> c
        leaf_key = parts[-1]
        if leaf_key != normalized:
            self._add_dynres(leaf_key, value)
            

    def _extract_item(self, item:dict[str,Any]) -> None:
        """
        Helper method to extract dynamic resources from a single item (json dict).
        """
        if not item:
            return
        for key, value in item.items():
            if isinstance(value, dict):
                self._extract_item(value)
            elif isinstance(value, list):
                for sub_item in value:
                    if isinstance(sub_item, dict):
                        self._extract_item(sub_item)
                    # TODO: how to handle non-dict items in a list? append each item or append the whole list?
                    # else:
                    #     self._add_dynres(key, value)
            else:
                self._add_dynres(key, value)
    
    def _add_dynres(self, key:str, value:Any) -> None:
        """
        Adds a dynamic resource to the pool.
        """
        if key not in self.pool:
            self.pool[key] = []
        if value not in self.pool[key]:
            self.pool[key].append(value)