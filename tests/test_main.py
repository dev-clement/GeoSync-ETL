import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.main import app

def test_health_check_operational():
    """
    Test the /health endpoint during a standard application lifecycle.
    
    This verifies that:
    1. The HTTP status is 200 (OK).
    2. The 'stac_client' was correctly initialized by the lifespan.
    3. The application metadata matches our settings.
    """
    # Using the 'with' keyword will trigger trhe @asynccontextmanager decorator lifespan (Startup / Shutdown)
    with TestClient(app) as client:
        response = client.get('/health')

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'operational'
        assert data['engine_status'] == 'connected'
        assert 'url' in data['connected_to'] or data['connected_to'] is not None

def test_search_satellite_data_success():
    """
    Test of the /search endpoint inside of the
    'try' part of it
    """
    with TestClient(app) as client:
        # 1. We creates a mock in order to simulate the STAC's items
        mock_item_1 = MagicMock()
        mock_item_2 = MagicMock()
        mock_item_1.id = 'S2A_MSIL2A_20240101'
        mock_item_2.id = 'S2A_MSIL2A_20240102'

        # 2. We are mocking the search_image from the intestor already present in app
        # Note: Ingestore has been stored in app.state.ingestor thanks to the lifespan
        client.app.state.ingestor.search_image = MagicMock(return_value=[mock_item_1, mock_item_2])

        # 3. Testing payload
        payload = {
            'bbox': [1.2, 43.5, 1.3, 3.6],
            'collections': ['sentinel-2-12a'],
            'datetime': "2024-01-01/2024-01-31",
            'limit': 2
        }

        response = client.post('/search', json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 2
        assert 'S2A_MSIL2A_20240101' in data['features']
        assert 'S2A_MSIL2A_20240102' in data['features']

def test_search_satellite_data_error_500():
    """
    Test for the 'except' block of the /search endpoint
    We simulate a break from the STAC catalog (exception)
    """
    with TestClient(app) as client:
        # 1. We are forcing the ingestor to raise an exception
        client.app.state.ingestor.search_image = MagicMock(
            side_effect=Exception("Connection Timeout")
        )

        payload = {
            'bbox': [1.2, 43.5, 1.3, 43.6],
            'datetime': '2024-01-01/2024-01-31'
        }

        response = client.post('/search', json=payload)

        # Verify the error code and the message
        assert response.status_code == 500
        assert response.json()['detail'] == 'Error: Cannot communicate with the catalog'

def test_lifespan_test_cleanup():
    """
    Test that the lifespan 'Destructor' phase cleans up resources.
    
    In a real-world CLS scenario, failing to nullify or close connections
    leads to memory leaks and socket exhaustion.
    """
    # Start the app
    with TestClient(app) as client:
        # Check that state is active while app is running
        assert client.app.state.stac_client is not None

    # After exiting the 'with' block, the shutdown phase should have run
    # Verification: Check if the state was cleared as defined in main.py
    assert client.app.state.stac_client is None

def test_health_without_lifespan():
    """
    Test the robustness of the /health endpoint if the state is missing.
    
    This simulates a partial failure where 'getattr' must handle a 
    missing attribute gracefully.
    """
    # Here we aren't using the with keyword, that means the lifespan won't be triggered here
    client = TestClient(app)
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json()['engine_status'] == 'disconnected'

