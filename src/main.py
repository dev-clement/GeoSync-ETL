from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from src.config import settings
from loguru import logger

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