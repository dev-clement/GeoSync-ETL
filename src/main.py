from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from src.config import settings
from src.ingestor import StacIngestor
from loguru import logger

# --- Data scheme (Validation Pydantic) ---

class SearchRequest(BaseModel):
    """
    Data Transfer Object (DTO) for satellite imagery search queries.

    This class serves as the validation layer for incoming POST requests to the 
    '/search' endpoint. It leverages Pydantic to ensure that the client provides 
    well-formatted geospatial and temporal parameters before the request reaches 
    the business logic.

    Purpose:
        1. Data Validation: Automatically rejects requests with missing or 
           malformed parameters (e.g., a bbox with 3 coordinates instead of 4).
        2. Documentation: Populates the OpenAPI/Swagger UI with expected 
           schemas and examples.
        3. Type Safety: Provides IDE auto-completion and static analysis 
           within the route handlers.

    Attributes:
        bbox (List[float]): A 4-element list representing the geographic 
            bounding box [min_lon, min_lat, max_lon, max_lat].
        collections (List[str]): IDs of the satellite constellations to 
            query (e.g., 'sentinel-2-l2a').
        datetime (str): RFC3339 formatted date-time or interval string.
        limit (int): Maximum number of items to return in a single page.
    """
    bbox: List[float] = Field(
        ..., 
        min_length=4, 
        max_length=4, 
        description="[min_long, min_lat, max_long, max_lat]"
    )
    collections: List[str] = Field(default=['sentinel-2-12a'])
    
    # Note: json_schema_extra is used for OpenAPI examples in Pydantic V2
    datetime: str = Field(
        ..., 
        json_schema_extra={"examples": ["2024-01-01/2024-01-31"]}
    )
    limit: int = Field(default=10, ge=1, le=100)

# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for the application lifespan.

    This replaces the deprecated startup and shutdown events. It provides a 
    clean, unified way to handle the application's lifecycle, acting as 
    both a constructor and a destructor.

    Startup logic (Constructor):
        Executed before the server starts accepting requests. This is the 
        ideal place to initialize shared resources, such as API clients 
        or database connections, and attach them to the 'app.state'.

    Shutdown logic (Destructor):
        Executed after the server receives a termination signal. This ensures 
        that all connections are closed gracefully and resources are released, 
        preventing memory leaks or hanging sockets.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    # ----------------------------------------------------
    # STARTUP (The "Constructor" phase)
    # ----------------------------------------------------
    logger.info(f'''🛰️  {settings.app_name} is launching...''')

    # Ingestor initialization (lazy loading)
    ingestor = StacIngestor(stac_api_url=settings.stac_api_url)

    # We store the instance in appliation state
    app.state.ingestor = ingestor

    logger.info(f'''Connecting to the STAC API: {settings.stac_api_url}''')

    # Initialization of the shared resource (e.g., a global http session)
    app.state.stac_client = { 'engine': 'connected', 'url': settings.stac_api_url }

    yield # App will run while it stays at this point

    # ----------------------------------------------------
    # SHUTDOWN (The "Destructor" phase)
    # ----------------------------------------------------
    logger.info(f'''🛑 Shutting down {settings.app_name}...''')
    logger.info(f'''Cleaning up connections and closing files''')
    app.state.stac_client = None
    app.state.ingestor = None

# --- Application ---

app = FastAPI(title=settings.app_name, lifespan=lifespan)

@app.get('/health')
async def health(request: Request):
    """
    Deep health check verifying service status and resource availability.

    This asynchronous method utilizes the 'Request' object to access the 
    application's shared state. Note that while 'request' is a parameter, 
    it is automatically injected by FastAPI and represents the incoming 
    HTTP context rather than a user-provided argument.

    Args:
        request (Request): The incoming HTTP request object, used to 
            retrieve the 'stac_client' from the application state.

    Returns:
        dict: A status report containing the mission name, engine connectivity 
            status, and the target API URL.
    """
    # We retrieve the client safely from the request state
    stac_info = getattr(request.app.state, 'stac_client', None)

    return {
        'status': 'operational',
        'mission': settings.app_name,
        'engine_status': stac_info['engine'] if stac_info else 'disconnected',
        'connected_to': stac_info['url'] if stac_info else None
    }

@app.post('/search')
async def search_satellite_data(request: Request, param: SearchRequest):
    """
    Endpoint for searching satellite imagery using the injected STAC ingestor.

    This asynchronous POST method acts as the entry point for geospatial queries.
    It retrieves the shared 'StacIngestor' instance from the application state,
    delegates the search logic to the service layer, and returns a summary 
    of the discovered satellite items.

    Args:
        request (Request): The incoming FastAPI request object used to access 
            the application's shared state (the Ingestor).
        param (SearchRequest): The validated search parameters provided in 
            the request body. Includes bounding box, collections, and dates.

    Returns:
        dict: A summary of the search results containing:
            - 'count' (int): The total number of images found.
            - 'features' (List[str]): A list of unique IDs for the discovered items.

    Raises:
        HTTPException: 
            - 500: If an error occurs while communicating with the STAC catalog.
    """
    ingestor: StacIngestor = request.app.state.ingestor

    try:
        # Call the business logic
        results = ingestor.search_image(
            bbox=param.bbox,
            collections=param.collections,
            datetime=param.datetime,
            limit=param.limit
        )

        # We fetch the number of images we found and the ids for test purpose
        items = list(results)
        return {
            "count": len(items),
            "features": [item.id for item in items]
        }
    except Exception as e:
        logger.error(f'''Error while searching in the STAC: {e}''')
        raise HTTPException(status_code=500, detail="Error: Cannot communicate with the catalog")