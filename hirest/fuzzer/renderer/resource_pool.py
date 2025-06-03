import logging, json
from typing import Any

logger = logging.getLogger(__name__)

class ResourcePool:
    """
    A class to manage a pool of dynamic resources for testing.
    """

    def __init__(self):
        self.pool:dict[str, list[Any]] = {}

    def extract_dynres(self, response:dict[str,Any]) -> None:
        """
        Extracts dynamic resources from the response JSON and stores them in the pool.
        """

        if not response or 'text' not in response or not response['text']:
            return 
        
        if not (response['status_code'] >= 200 and response['status_code'] < 300):
            return  
        
        response_json = response['text']
        if isinstance(response_json, str):
            try:
                response_json = json.loads(response_json)
            except json.JSONDecodeError:
                logger.warning("Failed to decode JSON response.")
                return

        if isinstance(response_json, list):
            for item in response_json:
                self._extract_item(item)
        elif isinstance(response_json, dict):
            self._extract_item(response_json)
        
        logger.debug(f"extracted dynamic resources: {self.pool}")
        
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