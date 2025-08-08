"""
Centralized API Management Service
Manages all external API connections and device-specific IP resolution
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum
import os
from services.netbox import netbox


class APIType(Enum):
    """Supported API types"""
    CATALYST_CENTER = "catalyst_center"
    MIST_CLOUD = "mist_cloud"
    ARISTA_CVP = "arista_cvp"
    JUNIPER_SPACE = "juniper_space"
    FORTINET_FORTIMANAGER = "fortinet_fortimanager"
    PALO_ALTO_PANORAMA = "palo_alto_panorama"
    DEVICE_SSH = "device_ssh"
    DEVICE_NETCONF = "device_netconf"
    DEVICE_RESTAPI = "device_restapi"


@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    name: str
    api_type: APIType
    base_url: str
    auth_method: str  # token, basic, certificate, oauth
    credentials: Dict[str, Any]
    version: Optional[str] = None
    enabled: bool = True
    timeout: int = 30
    retry_count: int = 3


class APIManager:
    """Centralized API management for all network operations"""
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
        self._load_api_configurations()
    
    def _load_api_configurations(self):
        """Load API configurations from environment or NetBox"""
        
        # Cisco Catalyst Center (DNA Center)
        if os.getenv("CATALYST_CENTER_URL"):
            self.endpoints["catalyst_center"] = APIEndpoint(
                name="Cisco Catalyst Center",
                api_type=APIType.CATALYST_CENTER,
                base_url=os.getenv("CATALYST_CENTER_URL"),
                auth_method="token",
                credentials={
                    "username": os.getenv("CATALYST_CENTER_USERNAME"),
                    "password": os.getenv("CATALYST_CENTER_PASSWORD"),
                    "client_id": os.getenv("CATALYST_CENTER_CLIENT_ID"),
                    "client_secret": os.getenv("CATALYST_CENTER_CLIENT_SECRET")
                },
                version="v1"
            )
        
        # Juniper Mist Cloud
        if os.getenv("MIST_CLOUD_TOKEN"):
            self.endpoints["mist_cloud"] = APIEndpoint(
                name="Juniper Mist Cloud",
                api_type=APIType.MIST_CLOUD,
                base_url="https://api.mist.com",
                auth_method="token",
                credentials={
                    "token": os.getenv("MIST_CLOUD_TOKEN"),
                    "org_id": os.getenv("MIST_ORG_ID")
                },
                version="v1"
            )
        
        # Arista CloudVision Portal (CVP)
        if os.getenv("ARISTA_CVP_URL"):
            self.endpoints["arista_cvp"] = APIEndpoint(
                name="Arista CloudVision Portal",
                api_type=APIType.ARISTA_CVP,
                base_url=os.getenv("ARISTA_CVP_URL"),
                auth_method="token",
                credentials={
                    "username": os.getenv("ARISTA_CVP_USERNAME"),
                    "password": os.getenv("ARISTA_CVP_PASSWORD")
                },
                version="v6"
            )
        
        # Juniper Space (for older Juniper devices)
        if os.getenv("JUNIPER_SPACE_URL"):
            self.endpoints["juniper_space"] = APIEndpoint(
                name="Juniper Space",
                api_type=APIType.JUNIPER_SPACE,
                base_url=os.getenv("JUNIPER_SPACE_URL"),
                auth_method="basic",
                credentials={
                    "username": os.getenv("JUNIPER_SPACE_USERNAME"),
                    "password": os.getenv("JUNIPER_SPACE_PASSWORD")
                }
            )
        
        # FortiNet FortiManager
        if os.getenv("FORTIMANAGER_URL"):
            self.endpoints["fortimanager"] = APIEndpoint(
                name="FortiNet FortiManager",
                api_type=APIType.FORTINET_FORTIMANAGER,
                base_url=os.getenv("FORTIMANAGER_URL"),
                auth_method="token",
                credentials={
                    "username": os.getenv("FORTIMANAGER_USERNAME"),
                    "password": os.getenv("FORTIMANAGER_PASSWORD")
                }
            )
        
        # Palo Alto Panorama
        if os.getenv("PANORAMA_URL"):
            self.endpoints["panorama"] = APIEndpoint(
                name="Palo Alto Panorama",
                api_type=APIType.PALO_ALTO_PANORAMA,
                base_url=os.getenv("PANORAMA_URL"),
                auth_method="token",
                credentials={
                    "api_key": os.getenv("PANORAMA_API_KEY")
                }
            )
    
    def get_endpoint(self, endpoint_name: str) -> Optional[APIEndpoint]:
        """Get API endpoint configuration"""
        return self.endpoints.get(endpoint_name)
    
    def get_device_management_ip(self, device_id: str) -> Optional[str]:
        """Get device management IP from NetBox"""
        try:
            device = netbox.get_device(device_id)
            if device and device.get("primary_ip4"):
                return device["primary_ip4"]["address"].split("/")[0]
            return None
        except Exception as e:
            print(f"Error getting device IP for {device_id}: {e}")
            return None
    
    def get_device_credentials(self, device_id: str) -> Dict[str, str]:
        """Get device credentials from NetBox secrets or default"""
        try:
            device = netbox.get_device(device_id)
            platform = device.get("platform", {}).get("slug", "")
            
            # Try to get device-specific credentials from NetBox secrets
            device_secrets = netbox.get_device_secrets(device_id)
            if device_secrets:
                return device_secrets
            
            # Fall back to platform-specific default credentials
            return self._get_platform_default_credentials(platform)
            
        except Exception as e:
            print(f"Error getting credentials for device {device_id}: {e}")
            return self._get_default_credentials()
    
    def _get_platform_default_credentials(self, platform: str) -> Dict[str, str]:
        """Get default credentials based on platform"""
        platform_credentials = {
            "cisco-ios": {
                "username": os.getenv("CISCO_DEFAULT_USERNAME", "admin"),
                "password": os.getenv("CISCO_DEFAULT_PASSWORD", "admin"),
                "enable_password": os.getenv("CISCO_ENABLE_PASSWORD", "")
            },
            "cisco-nxos": {
                "username": os.getenv("CISCO_NXOS_USERNAME", "admin"),
                "password": os.getenv("CISCO_NXOS_PASSWORD", "admin")
            },
            "juniper-junos": {
                "username": os.getenv("JUNIPER_USERNAME", "admin"),
                "password": os.getenv("JUNIPER_PASSWORD", "admin")
            },
            "arista-eos": {
                "username": os.getenv("ARISTA_USERNAME", "admin"),
                "password": os.getenv("ARISTA_PASSWORD", "admin")
            }
        }
        
        return platform_credentials.get(platform, self._get_default_credentials())
    
    def _get_default_credentials(self) -> Dict[str, str]:
        """Get default fallback credentials"""
        return {
            "username": "admin",
            "password": "admin"
        }
    
    def should_use_centralized_api(self, device_id: str) -> tuple[bool, Optional[str]]:
        """Determine if device should use centralized API vs direct connection"""
        try:
            device = netbox.get_device(device_id)
            if not device:
                return False, None
            
            platform = device.get("platform", {}).get("slug", "")
            manufacturer = device.get("device_type", {}).get("manufacturer", {}).get("slug", "")
            
            # Check if device is managed by Catalyst Center
            if manufacturer == "cisco" and any(endpoint in self.endpoints for endpoint in ["catalyst_center"]):
                # Check if device is in Catalyst Center inventory
                if self._device_in_catalyst_center(device_id):
                    return True, "catalyst_center"
            
            # Check if device is managed by Mist Cloud (for Juniper wireless)
            if manufacturer == "juniper" and "mist_cloud" in self.endpoints:
                device_role = device.get("device_role", {}).get("slug", "")
                if "access-point" in device_role or "wireless" in device_role:
                    return True, "mist_cloud"
            
            # Check if device is managed by Arista CVP
            if manufacturer == "arista" and "arista_cvp" in self.endpoints:
                if self._device_in_arista_cvp(device_id):
                    return True, "arista_cvp"
            
            # Check if device is managed by FortiManager
            if manufacturer == "fortinet" and "fortimanager" in self.endpoints:
                return True, "fortimanager"
            
            # Check if device is managed by Panorama
            if manufacturer == "paloaltonetworks" and "panorama" in self.endpoints:
                return True, "panorama"
            
            # Default to direct device connection
            return False, None
            
        except Exception as e:
            print(f"Error determining API method for device {device_id}: {e}")
            return False, None
    
    def _device_in_catalyst_center(self, device_id: str) -> bool:
        """Check if device exists in Catalyst Center inventory"""
        try:
            # This would make actual API call to Catalyst Center
            # For now, return True if Catalyst Center is configured
            return "catalyst_center" in self.endpoints
        except:
            return False
    
    def _device_in_arista_cvp(self, device_id: str) -> bool:
        """Check if device exists in Arista CVP inventory"""
        try:
            # This would make actual API call to CVP
            # For now, return True if CVP is configured
            return "arista_cvp" in self.endpoints
        except:
            return False
    
    def get_connection_info(self, device_id: str) -> Dict[str, Any]:
        """Get complete connection information for a device"""
        use_centralized, api_name = self.should_use_centralized_api(device_id)
        
        connection_info = {
            "device_id": device_id,
            "use_centralized_api": use_centralized,
            "api_endpoint": api_name,
            "device_ip": self.get_device_management_ip(device_id),
            "credentials": self.get_device_credentials(device_id)
        }
        
        if use_centralized and api_name:
            connection_info["endpoint_config"] = self.get_endpoint(api_name)
        
        return connection_info
    
    def list_available_endpoints(self) -> List[Dict[str, Any]]:
        """List all configured API endpoints"""
        return [
            {
                "name": endpoint.name,
                "type": endpoint.api_type.value,
                "base_url": endpoint.base_url,
                "enabled": endpoint.enabled,
                "version": endpoint.version
            }
            for endpoint in self.endpoints.values()
        ]
    
    def validate_endpoint_connectivity(self, endpoint_name: str) -> Dict[str, Any]:
        """Test connectivity to an API endpoint"""
        endpoint = self.get_endpoint(endpoint_name)
        if not endpoint:
            return {"status": "error", "message": f"Endpoint {endpoint_name} not found"}
        
        try:
            # This would implement actual connectivity tests
            # For now, return basic validation
            return {
                "status": "success",
                "endpoint": endpoint_name,
                "base_url": endpoint.base_url,
                "reachable": True,
                "response_time_ms": 50  # Mock response time
            }
        except Exception as e:
            return {
                "status": "error", 
                "endpoint": endpoint_name,
                "message": str(e)
            }


# Global API manager instance
api_manager = APIManager()


# Convenience functions for workflows
def get_device_connection(device_id: str) -> Dict[str, Any]:
    """Get device connection information"""
    return api_manager.get_connection_info(device_id)


def get_api_endpoint(endpoint_name: str) -> Optional[APIEndpoint]:
    """Get API endpoint configuration"""
    return api_manager.get_endpoint(endpoint_name)


def should_use_centralized_management(device_id: str) -> bool:
    """Check if device should use centralized management"""
    use_centralized, _ = api_manager.should_use_centralized_api(device_id)
    return use_centralized
