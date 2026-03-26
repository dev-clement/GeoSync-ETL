"""
Configuration module for the GeoSync-ETL processing chain.

This module provides a centralized, validated configuration object that 
interfaces with environment variables for satellite data processing.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application-wide settings and environment validator.

    This class defines the schema for the application's configuration. It 
    utilizes Pydantic to enforce type constraints and ensure that all 
    required parameters (like API URLs) are present before execution.

    Attributes:
        app_name (str): The name of the application.
        stac_api_url (str): The URL endpoint for the STAC catalog API.
        tile_size (int): The pixel dimension for tiled raster processing.
    """

    app_name: str = "GeoSync-ETL"
    stac_api_url: str
    title_size: int = 256
    model_config: SettingsConfigDict = SettingsConfigDict(env_file='.env')

    def __init__(self, **data):
        """
        Initializes the Settings object and triggers environment validation.

        Args:
            **data: Arbitrary keyword arguments passed to the Pydantic 
                BaseSettings constructor.
        
        Raises:
            ValidationError: If required environment variables are missing 
                or fail type validation.
        """
        super().__init__(**data)


settings = Settings()