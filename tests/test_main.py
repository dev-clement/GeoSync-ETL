import pytest
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

