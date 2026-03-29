from pystac_client import Client
from typing import List, Optional, Any
from loguru import logger

class StacIngestor:
    """
    Service responsible for interfacing the program with the STAC API
    """
    def __init__(self, stac_api_url: str):
        """
        Ingestor initialization with the api_stac url
        """
        self.api_url = stac_api_url
        self._client: Optional[Client] = None
    
    def _get_client(self) -> Client:
        """
        Initialize the client in lazy-loading method
        """
        if self._client is None:
            logger.info(f'''Opening connection to STAC API {self.api_url}''')
            self._client = Client.open(self.api_url)
        return self._client
    
    def search_image(self, bbox: List[float], collections: List[str], datetime: str, limit: int = 10) -> Any:
        """
        Launch a request for searching on the STAC catalog
        """
        client = self._get_client()

        logger.info(f'''Searching {collections} in {bbox} for period {datetime}''')

        # Prepare the query
        search = client.search(
            collections=collections,
            bbox=bbox,
            datetime=datetime,
            limit=limit
        )

        # item_collectio() executes the network request
        return search.item_collection()
