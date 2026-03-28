### Context & Problem Statement
Currently, the GeoSync-ETL application has a robust orchestration layer and health monitoring, but it lacks the capability to actually interact with satellite data providers. To fulfill the mission of synchronizing geospatial data, we need a dedicated service that can query SpatioTemporal Asset Catalogs (STAC).

### Why do we need this?

1. Abstraction: The application should not be tightly coupled to the low-level networking of pystac-client. We need a "Service Layer" (the Ingestor) to handle the translation between our business requirements and the API's technical requirements.
2. Efficiency: By implementing a dedicated Ingestor with "Lazy Loading" (initializing the client only when needed), we optimize resource usage and startup time.
3. Maintainability: If the data provider changes (e.g., switching from Microsoft Planetary Computer to another catalog), we should only need to modify this one file.

### Technical objective
The goal is to create src/ingestor.py containing a StacIngestor class that performs the following:
- Protocol Management: Encapsulate the pystac_client.Client logic.
- Spatial Queries: Implement a search_images method accepting a Bounding Box (bbox) to target specific geographic areas.
- Temporal Queries: Support datetime parameters to filter imagery by date ranges or specific timestamps.
- Catalog Filtering: Allow targeting specific satellite constellations (e.g., sentinel-2-l2a).

### Implementation Details
This service will utilize
- **Library**: pystac-client for standard-compliant API communication.
- **Architecture**: A Python class-based approach to allow for easy dependency injection into FastAPI routes later.
- **Logging**: Integrated loguru reporting to track search parameters and API latency.

### Definition of Done (DoD)
- [x] `src/ingestor.py` is created with the `StacIngestor` class.
- [x] `pystac-client` is added to requirements.txt.
- [x] The ingestor successfully retrieves an `ItemCollection` from the Microsoft Planetary Computer.
- [x] A unit test verifies the ingestor's search capabilities.

### Understanding the StacIngestor Logic

The StacIngestor class is a Service Layer. Its job is to hide the complexity of the pystac-client library from the rest of your application.

1. The Constructor (__init__)
```python
def __init__(self, stac_api_url: str):
    self.api_url = stac_api_url
    self._client: Optional[Client] = None
```
`self.api_url`: We store the URL but we don't connect yet.

`self._client = None`: This is a placeholder. We don't want to open a network connection the microsecond the object is created. Why? Because if you create 100 ingestors in a test, you don't want 100 open sockets crashing your machine.

2. The Lazy Loader (_get_client)
This is a classic "Creational Pattern."
```python
def _get_client(self) -> Client:
    if self._client is None:
        logger.info(f"Opening connection...")
        self._client = Client.open(self.api_url)
    return self._client
```
"Lazy Loading": We only call `Client.open()` the very first time someone actually tries to search for something.

Singleton-ish behavior: Once `self._client` is set, every subsequent call to `_get_client` simply returns the existing connection. It’s efficient and prevents redundant network handshakes.

3. The Orchestrator (search_image)
This method translates "Business Language" into "Satellite Language."

#### Step A: Get the connection
```python
client = self._get_client()
```

We use our internal helper to ensure we have a valid connection before proceeding.

#### Step B: The Query Preparation (search)

```python
search = client.search(
    collections=collections,
    bbox=bbox,
    datetime=datetime,
    limit=limit
)
```

`client.search` does NOT hit the network to get images yet. It validates your parameters and prepares a "Search Object" (a query plan).

#### Step C: The Execution (item_collection)
```python
return search.item_collection()
```
`item_collection()` is the moment the "Enter" key is pressed. It sends the request to Microsoft, waits for the GeoJSON response, and parses it into Python objects.

##### Why this conclusion?
We arrived at this specific code because:

Separation of Concerns: Your FastAPI routes won't know that pystac-client exists. They just know StacIngestor has a search_image method.
Testability: Because we have a clear _get_client method, we were able to "mock" it in our tests to simulate the API without actually needing the internet.

Robustness: Using Optional[Client] and Type Hints ensures that IDEs (like VS Code) give you the right autocomplete and catch errors before you run the code.