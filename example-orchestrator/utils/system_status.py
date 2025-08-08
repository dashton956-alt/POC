"""
System status utilities for Intent Based Orchestrator
"""
import requests
import logging
from typing import Dict, Any
from settings import Settings

logger = logging.getLogger(__name__)
settings = Settings()

def get_system_status() -> Dict[str, Any]:
    """Get status of orchestrator and NetBox systems."""
    status = {
        "orchestrator": {
            "name": "Intent Based Orchestrator",
            "status": "running",
            "description": "Network Intent-Based Orchestration Platform",
            "url": "http://localhost:8080"
        },
        "netbox": {
            "name": "NetBox DCIM",
            "status": "unknown",
            "description": "Data Center Infrastructure Management",
            "url": "http://localhost:8000"
        }
    }
    
    # Check NetBox status
    try:
        netbox_url = getattr(settings, 'NETBOX_URL', 'http://127.17.0.1:8000')
        response = requests.get(f"{netbox_url}/api/", timeout=5)
        if response.status_code == 200:
            status["netbox"]["status"] = "running"
            status["netbox"]["version"] = response.headers.get("API-Version", "unknown")
        else:
            status["netbox"]["status"] = "error"
    except Exception as e:
        logger.warning(f"Could not check NetBox status: {e}")
        status["netbox"]["status"] = "unreachable"
    
    return status
