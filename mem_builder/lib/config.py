import os
from daytona import DaytonaConfig

def get_daytona_config():
    # Using explicit configuration
    config = DaytonaConfig(
        api_key=os.getenv("DAYTONA_API_KEY", "your-api-key"),
        api_url=os.getenv("DAYTONA_API_URL", "https://app.daytona.io/api"),
        target=os.getenv("DAYTONA_TARGET", "us"),
    )
    return config
