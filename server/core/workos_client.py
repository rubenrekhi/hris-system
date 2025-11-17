"""
workos_client.py
----------------
Initialize and configure the WorkOS client for authentication.
"""

import os
from workos import WorkOSClient

# Initialize WorkOS client with credentials from environment variables
workos_client = WorkOSClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID")
)
