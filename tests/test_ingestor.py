import pytest
from unittest.mock import MagicMock, patch
from src.ingestor import StacIngestor

def test_get_client_lazy_initialization():
    """
    Test that _get_client initializes the Client only once (Lazy loading)
    """
    api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
    ingestor = StacIngestor(stac_api_url=api_url)
 
    # We patch the Client class in the ingestor module
    with patch("src.ingestor.Client.open") as mock_open:
        # Configure the mock to return a dummy client object
        mock_client_instance = MagicMock()
        mock_open.return_value = mock_client_instance

        # The first call should trigger Client.open()
        client1 = ingestor._get_client()
        mock_open.assert_called_once()
        assert client1 == mock_client_instance

        # Second call: Should not trigger the Client.open() again, it should return the cached client
        client2 = ingestor._get_client()
        mock_open.assert_called_once()
        assert client2 == mock_client_instance
        assert ingestor._client is not None

def test_set_images_workflow():
    """
    Test the search image method by mocking the client's search and 
    item_collection methods
    """
    ingestor = StacIngestor("http://dummy-api.com")

    # 1. Create the mock hierarchy
    mock_client = MagicMock()
    mock_search_obj = MagicMock()
    mock_item_collection = MagicMock()

    # 2. Setup the behavior: client.search() -> search_obj -> search_obj.item_collection() -> results
    mock_client.search.return_value = mock_search_obj
    mock_search_obj.item_collection.return_value = mock_item_collection

    # 3. Inject the mock client into the ingestor se we don't trigger real network calls
    ingestor._client = mock_client

    # 4. Parameters for the search
    test_param = {
        'bbox': [1.0, 43.0, 1.5, 43.5],
        'collections': ['sentinel-2-12a'],
        'datetime': '2024-01-01/2024-01-02',
        'limit': 5
    }

    # 5. Execute the search
    results = ingestor.search_image(**test_param)

    # 6. Verification
    # Check that search was called with exactly the 4 parameters
    mock_client.search.assert_called_once_with(
        collections=test_param['collections'],
        bbox=test_param['bbox'],
        datetime=test_param['datetime'],
        limit=test_param['limit']
    )

    # Check that item_collection was called on the object returned by search
    mock_search_obj.item_collection.assert_called_once()

    # Verify we returned the mock collection
    assert results == mock_item_collection