"""
Device Connection Service
Handles connections to network devices via various methods (SSH, NETCONF, REST API, or centralized management)
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio
import json

from services.api_manager import api_manager, APIType
from services.netbox import netbox


@dataclass
class ConnectionResult:
    """Result of device connection attempt"""
    success: bool
    method: str
    endpoint: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class DeviceConnector(ABC):
    """Abstract base class for device connectors"""
    
    @abstractmethod
    async def connect(self, device_id: str, **kwargs) -> ConnectionResult:
        pass
    
    @abstractmethod
    async def execute_command(self, device_id: str, command: str, **kwargs) -> ConnectionResult:
        pass
    
    @abstractmethod
    async def deploy_configuration(self, device_id: str, config: str, **kwargs) -> ConnectionResult:
        pass


class CatalystCenterConnector(DeviceConnector):
    """Cisco Catalyst Center API connector"""
    
    def __init__(self):
        self.endpoint = api_manager.get_endpoint("catalyst_center")
    
    async def connect(self, device_id: str, **kwargs) -> ConnectionResult:
        """Connect via Catalyst Center API"""
        if not self.endpoint:
            return ConnectionResult(
                success=False,
                method="catalyst_center",
                message="Catalyst Center endpoint not configured"
            )
        
        try:
            # Get device info from NetBox to map to Catalyst Center
            device = netbox.get_device(device_id)
            device_ip = api_manager.get_device_management_ip(device_id)
            
            # Mock Catalyst Center device lookup
            catalyst_device = await self._find_device_in_catalyst_center(device_ip)
            
            if catalyst_device:
                return ConnectionResult(
                    success=True,
                    method="catalyst_center",
                    endpoint=self.endpoint.base_url,
                    data={"catalyst_device_id": catalyst_device["id"]}
                )
            else:
                return ConnectionResult(
                    success=False,
                    method="catalyst_center",
                    message=f"Device {device_ip} not found in Catalyst Center"
                )
                
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="catalyst_center",
                message=f"Catalyst Center connection error: {str(e)}"
            )
    
    async def execute_command(self, device_id: str, command: str, **kwargs) -> ConnectionResult:
        """Execute command via Catalyst Center"""
        connection = await self.connect(device_id)
        if not connection.success:
            return connection
        
        try:
            # Mock command execution via Catalyst Center
            result = await self._execute_catalyst_center_command(
                connection.data["catalyst_device_id"], 
                command
            )
            
            return ConnectionResult(
                success=True,
                method="catalyst_center",
                endpoint=self.endpoint.base_url,
                data={"output": result}
            )
            
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="catalyst_center",
                message=f"Command execution error: {str(e)}"
            )
    
    async def deploy_configuration(self, device_id: str, config: str, **kwargs) -> ConnectionResult:
        """Deploy configuration via Catalyst Center template"""
        connection = await self.connect(device_id)
        if not connection.success:
            return connection
        
        try:
            # Use Catalyst Center template deployment
            deployment_id = await self._deploy_catalyst_center_template(
                connection.data["catalyst_device_id"],
                config,
                kwargs.get("template_name", "custom_config")
            )
            
            return ConnectionResult(
                success=True,
                method="catalyst_center",
                endpoint=self.endpoint.base_url,
                data={"deployment_id": deployment_id}
            )
            
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="catalyst_center",
                message=f"Configuration deployment error: {str(e)}"
            )
    
    async def _find_device_in_catalyst_center(self, device_ip: str) -> Optional[Dict]:
        """Find device in Catalyst Center by IP"""
        # Mock implementation - would use actual Catalyst Center API
        return {
            "id": f"cc-device-{device_ip.replace('.', '-')}",
            "managementIpAddress": device_ip,
            "hostname": f"device-{device_ip}",
            "reachabilityStatus": "Reachable"
        }
    
    async def _execute_catalyst_center_command(self, catalyst_device_id: str, command: str) -> str:
        """Execute command via Catalyst Center API"""
        # Mock implementation
        return f"Command '{command}' executed on {catalyst_device_id}"
    
    async def _deploy_catalyst_center_template(self, catalyst_device_id: str, config: str, template_name: str) -> str:
        """Deploy configuration template via Catalyst Center"""
        # Mock implementation
        deployment_id = f"deploy-{catalyst_device_id}-{hash(config) % 10000}"
        return deployment_id


class MistCloudConnector(DeviceConnector):
    """Juniper Mist Cloud API connector"""
    
    def __init__(self):
        self.endpoint = api_manager.get_endpoint("mist_cloud")
    
    async def connect(self, device_id: str, **kwargs) -> ConnectionResult:
        """Connect via Mist Cloud API"""
        if not self.endpoint:
            return ConnectionResult(
                success=False,
                method="mist_cloud",
                message="Mist Cloud endpoint not configured"
            )
        
        try:
            device = netbox.get_device(device_id)
            device_mac = device.get("custom_fields", {}).get("mac_address")
            
            if not device_mac:
                return ConnectionResult(
                    success=False,
                    method="mist_cloud",
                    message="Device MAC address required for Mist Cloud connection"
                )
            
            # Mock Mist device lookup
            mist_device = await self._find_device_in_mist(device_mac)
            
            if mist_device:
                return ConnectionResult(
                    success=True,
                    method="mist_cloud",
                    endpoint=self.endpoint.base_url,
                    data={"mist_device_id": mist_device["id"]}
                )
            else:
                return ConnectionResult(
                    success=False,
                    method="mist_cloud",
                    message=f"Device {device_mac} not found in Mist Cloud"
                )
                
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="mist_cloud",
                message=f"Mist Cloud connection error: {str(e)}"
            )
    
    async def execute_command(self, device_id: str, command: str, **kwargs) -> ConnectionResult:
        """Execute command via Mist Cloud API"""
        connection = await self.connect(device_id)
        if not connection.success:
            return connection
        
        try:
            # Mist doesn't support arbitrary commands, but supports specific operations
            result = await self._execute_mist_operation(
                connection.data["mist_device_id"],
                command
            )
            
            return ConnectionResult(
                success=True,
                method="mist_cloud",
                endpoint=self.endpoint.base_url,
                data={"result": result}
            )
            
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="mist_cloud",
                message=f"Mist operation error: {str(e)}"
            )
    
    async def deploy_configuration(self, device_id: str, config: str, **kwargs) -> ConnectionResult:
        """Deploy configuration via Mist Cloud"""
        connection = await self.connect(device_id)
        if not connection.success:
            return connection
        
        try:
            # Deploy via Mist configuration update
            update_id = await self._update_mist_device_config(
                connection.data["mist_device_id"],
                json.loads(config)  # Mist uses JSON configuration
            )
            
            return ConnectionResult(
                success=True,
                method="mist_cloud",
                endpoint=self.endpoint.base_url,
                data={"update_id": update_id}
            )
            
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="mist_cloud",
                message=f"Mist configuration update error: {str(e)}"
            )
    
    async def _find_device_in_mist(self, device_mac: str) -> Optional[Dict]:
        """Find device in Mist by MAC address"""
        # Mock implementation
        return {
            "id": f"mist-{device_mac.replace(':', '')}",
            "mac": device_mac,
            "name": f"AP-{device_mac[-5:]}",
            "connected": True
        }
    
    async def _execute_mist_operation(self, mist_device_id: str, operation: str) -> Dict:
        """Execute Mist-specific operation"""
        # Mock implementation
        return {"operation": operation, "device": mist_device_id, "status": "completed"}
    
    async def _update_mist_device_config(self, mist_device_id: str, config: Dict) -> str:
        """Update Mist device configuration"""
        # Mock implementation
        return f"update-{mist_device_id}-{hash(str(config)) % 10000}"


class DirectSSHConnector(DeviceConnector):
    """Direct SSH connection to network devices"""
    
    async def connect(self, device_id: str, **kwargs) -> ConnectionResult:
        """Connect via direct SSH"""
        try:
            device_ip = api_manager.get_device_management_ip(device_id)
            credentials = api_manager.get_device_credentials(device_id)
            
            if not device_ip:
                return ConnectionResult(
                    success=False,
                    method="direct_ssh",
                    message="Device management IP not available"
                )
            
            # Mock SSH connection test
            ssh_available = await self._test_ssh_connectivity(device_ip, credentials)
            
            if ssh_available:
                return ConnectionResult(
                    success=True,
                    method="direct_ssh",
                    endpoint=device_ip,
                    data={"host": device_ip, "credentials": credentials}
                )
            else:
                return ConnectionResult(
                    success=False,
                    method="direct_ssh",
                    message=f"SSH connection failed to {device_ip}"
                )
                
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="direct_ssh",
                message=f"SSH connection error: {str(e)}"
            )
    
    async def execute_command(self, device_id: str, command: str, **kwargs) -> ConnectionResult:
        """Execute command via direct SSH"""
        connection = await self.connect(device_id)
        if not connection.success:
            return connection
        
        try:
            # Mock SSH command execution
            output = await self._execute_ssh_command(
                connection.data["host"],
                connection.data["credentials"],
                command
            )
            
            return ConnectionResult(
                success=True,
                method="direct_ssh",
                endpoint=connection.data["host"],
                data={"command": command, "output": output}
            )
            
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="direct_ssh",
                message=f"SSH command execution error: {str(e)}"
            )
    
    async def deploy_configuration(self, device_id: str, config: str, **kwargs) -> ConnectionResult:
        """Deploy configuration via direct SSH"""
        connection = await self.connect(device_id)
        if not connection.success:
            return connection
        
        try:
            # Deploy configuration via SSH
            result = await self._deploy_ssh_configuration(
                connection.data["host"],
                connection.data["credentials"],
                config
            )
            
            return ConnectionResult(
                success=True,
                method="direct_ssh",
                endpoint=connection.data["host"],
                data={"deployed": True, "result": result}
            )
            
        except Exception as e:
            return ConnectionResult(
                success=False,
                method="direct_ssh",
                message=f"SSH configuration deployment error: {str(e)}"
            )
    
    async def _test_ssh_connectivity(self, host: str, credentials: Dict) -> bool:
        """Test SSH connectivity to device"""
        # Mock implementation
        return True
    
    async def _execute_ssh_command(self, host: str, credentials: Dict, command: str) -> str:
        """Execute SSH command"""
        # Mock implementation
        return f"Output from {host}: {command} executed successfully"
    
    async def _deploy_ssh_configuration(self, host: str, credentials: Dict, config: str) -> Dict:
        """Deploy configuration via SSH"""
        # Mock implementation
        return {"lines_applied": len(config.split('\n')), "status": "success"}


class DeviceConnectionManager:
    """Main device connection manager that chooses appropriate connection method"""
    
    def __init__(self):
        self.connectors = {
            "catalyst_center": CatalystCenterConnector(),
            "mist_cloud": MistCloudConnector(),
            "direct_ssh": DirectSSHConnector()
        }
    
    async def get_optimal_connector(self, device_id: str) -> DeviceConnector:
        """Get the best connector for a device"""
        try:
            use_centralized, api_name = api_manager.should_use_centralized_api(device_id)
            
            if use_centralized and api_name in self.connectors:
                return self.connectors[api_name]
            else:
                return self.connectors["direct_ssh"]
                
        except Exception as e:
            print(f"Error determining connector for device {device_id}: {e}")
            return self.connectors["direct_ssh"]
    
    async def connect_to_device(self, device_id: str, **kwargs) -> ConnectionResult:
        """Connect to device using optimal method"""
        connector = await self.get_optimal_connector(device_id)
        return await connector.connect(device_id, **kwargs)
    
    async def execute_device_command(self, device_id: str, command: str, **kwargs) -> ConnectionResult:
        """Execute command on device"""
        connector = await self.get_optimal_connector(device_id)
        return await connector.execute_command(device_id, command, **kwargs)
    
    async def deploy_device_configuration(self, device_id: str, config: str, **kwargs) -> ConnectionResult:
        """Deploy configuration to device"""
        connector = await self.get_optimal_connector(device_id)
        return await connector.deploy_configuration(device_id, config, **kwargs)
    
    async def test_device_connectivity(self, device_id: str) -> Dict[str, Any]:
        """Test all available connection methods for a device"""
        results = {}
        
        # Test centralized API if available
        use_centralized, api_name = api_manager.should_use_centralized_api(device_id)
        if use_centralized and api_name in self.connectors:
            connector = self.connectors[api_name]
            result = await connector.connect(device_id)
            results[api_name] = {
                "success": result.success,
                "method": result.method,
                "endpoint": result.endpoint,
                "message": result.message
            }
        
        # Always test direct SSH as fallback
        ssh_connector = self.connectors["direct_ssh"]
        ssh_result = await ssh_connector.connect(device_id)
        results["direct_ssh"] = {
            "success": ssh_result.success,
            "method": ssh_result.method,
            "endpoint": ssh_result.endpoint,
            "message": ssh_result.message
        }
        
        return results


# Global connection manager instance
device_connection_manager = DeviceConnectionManager()


# Convenience functions for workflows
async def connect_to_device(device_id: str, **kwargs) -> ConnectionResult:
    """Connect to device using optimal method"""
    return await device_connection_manager.connect_to_device(device_id, **kwargs)


async def execute_device_command(device_id: str, command: str, **kwargs) -> ConnectionResult:
    """Execute command on device"""
    return await device_connection_manager.execute_device_command(device_id, command, **kwargs)


async def deploy_device_configuration(device_id: str, config: str, **kwargs) -> ConnectionResult:
    """Deploy configuration to device"""
    return await device_connection_manager.deploy_device_configuration(device_id, config, **kwargs)
