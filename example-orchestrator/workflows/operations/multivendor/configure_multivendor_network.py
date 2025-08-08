"""
Multi-Vendor Network Configuration Workflow
Demonstrates centralized API management with automatic platform detection and optimal connection methods
"""

from orchestrator import workflow
from orchestrator.forms import FormPage
from orchestrator.targets import Target
from orchestrator.types import State, SubscriptionLifecycle, UUIDstr
from orchestrator.workflow import Step, StepList, begin, done
from orchestrator.workflows.steps import store_process_subscription
from pydantic import Field
from pydantic_forms.core import FormPage
from pydantic_forms.types import Choice
from typing import List, Dict, Any, Optional
import asyncio

from products.product_types.multivendor import MultiVendorInactive, MultiVendorProvisioning
from services.netbox import netbox
from services.api_manager import api_manager, get_device_connection, APIType
from services.device_connector import device_connection_manager, connect_to_device, execute_device_command, deploy_device_configuration
from workflows.shared import device_selector


class MultiVendorConfigurationForm(FormPage):
    """Multi-vendor network configuration form with automatic API selection"""
    
    # Device Selection - NetBox driven with platform awareness
    target_devices: List[str] = Field(
        description="Target Devices (all vendors supported)",
        min_items=1,
        choices=get_all_network_devices_from_netbox()
    )
    
    # Configuration Type
    configuration_type: Choice = Field(
        description="Configuration Type",
        choices=[
            ("interface_config", "Interface Configuration"),
            ("vlan_config", "VLAN Configuration"),
            ("routing_config", "Basic Routing"),
            ("security_config", "Security Settings"),
            ("monitoring_config", "Monitoring Setup"),
            ("custom_config", "Custom Configuration")
        ],
        default="interface_config"
    )
    
    # Interface Configuration (when applicable)
    interface_name: Optional[str] = Field(
        description="Interface Name (e.g., GigabitEthernet0/1, et-0/0/1, Ethernet1/1)",
        default=None
    )
    
    interface_description: Optional[str] = Field(
        description="Interface Description",
        default="Configured via Multi-Vendor Orchestrator"
    )
    
    interface_vlan: Optional[int] = Field(
        description="VLAN ID",
        ge=1,
        le=4094,
        default=None
    )
    
    # VLAN Configuration (when applicable)
    vlan_id: Optional[int] = Field(
        description="VLAN ID to configure",
        ge=1,
        le=4094,
        default=None
    )
    
    vlan_name: Optional[str] = Field(
        description="VLAN Name",
        default=None
    )
    
    # Custom Configuration
    custom_config: Optional[str] = Field(
        description="Custom Configuration Commands",
        default=None
    )
    
    # Deployment Options
    test_connectivity_first: bool = Field(
        description="Test all connectivity methods before deployment",
        default=True
    )
    
    use_centralized_apis: bool = Field(
        description="Prefer centralized API management (Catalyst Center, Mist, CVP, etc.)",
        default=True
    )
    
    backup_before_change: bool = Field(
        description="Backup current configuration before changes",
        default=True
    )
    
    validate_after_deployment: bool = Field(
        description="Validate configuration after deployment",
        default=True
    )


@dataclass
class MultiVendorConfigurationProvisioning(MultiVendorInactive):
    """Multi-vendor configuration provisioning state"""
    
    target_devices: List[str]
    configuration_type: str
    interface_name: Optional[str] = None
    interface_description: Optional[str] = None
    interface_vlan: Optional[int] = None
    vlan_id: Optional[int] = None
    vlan_name: Optional[str] = None
    custom_config: Optional[str] = None
    test_connectivity_first: bool = True
    use_centralized_apis: bool = True
    backup_before_change: bool = True
    validate_after_deployment: bool = True
    
    # Runtime state
    device_info: List[Dict[str, Any]] = field(default_factory=list)
    connectivity_tests: Dict[str, Any] = field(default_factory=dict)
    api_endpoint_status: Dict[str, Any] = field(default_factory=dict)
    deployment_results: List[Dict[str, Any]] = field(default_factory=list)
    validation_results: List[Dict[str, Any]] = field(default_factory=list)


@workflow("Multi-Vendor Network Configuration", initial_input_form=MultiVendorConfigurationForm)
def configure_multivendor_network() -> StepList:
    return begin >> analyze_target_devices >> test_api_connectivity >> deploy_configurations >> validate_deployment >> done


@configure_multivendor_network.step("Analyze Target Devices and API Endpoints")
def analyze_target_devices(subscription: MultiVendorConfigurationProvisioning) -> State:
    """Analyze target devices and determine optimal API endpoints"""
    
    device_info = []
    api_endpoints_needed = set()
    
    for device_id in subscription.target_devices:
        try:
            # Get device information from NetBox
            device = netbox.get_device(device_id)
            if not device:
                continue
            
            # Get connection information
            connection_info = get_device_connection(device_id)
            
            # Determine manufacturer and platform
            manufacturer = device.get("device_type", {}).get("manufacturer", {}).get("slug", "unknown")
            platform = device.get("platform", {}).get("slug", "unknown")
            
            # Add to endpoints needed
            if connection_info["use_centralized_api"] and connection_info["api_endpoint"]:
                api_endpoints_needed.add(connection_info["api_endpoint"])
            
            device_info.append({
                "device_id": device_id,
                "name": device["name"],
                "manufacturer": manufacturer,
                "platform": platform,
                "site": device.get("site", {}).get("name", "Unknown"),
                "device_role": device.get("device_role", {}).get("name", "Unknown"),
                "management_ip": connection_info.get("device_ip"),
                "connection_method": "Centralized API" if connection_info["use_centralized_api"] else "Direct SSH",
                "api_endpoint": connection_info.get("api_endpoint"),
                "connection_info": connection_info
            })
            
        except Exception as e:
            device_info.append({
                "device_id": device_id,
                "error": str(e),
                "connection_method": "Error"
            })
    
    subscription.device_info = device_info
    subscription.api_endpoints_needed = list(api_endpoints_needed)
    
    # Create deployment summary
    subscription.deployment_plan = {
        "total_devices": len(device_info),
        "cisco_devices": len([d for d in device_info if d.get("manufacturer") == "cisco"]),
        "juniper_devices": len([d for d in device_info if d.get("manufacturer") == "juniper"]),
        "arista_devices": len([d for d in device_info if d.get("manufacturer") == "arista"]),
        "other_devices": len([d for d in device_info if d.get("manufacturer") not in ["cisco", "juniper", "arista"]]),
        "centralized_api_devices": len([d for d in device_info if d.get("connection_method") == "Centralized API"]),
        "direct_ssh_devices": len([d for d in device_info if d.get("connection_method") == "Direct SSH"]),
        "api_endpoints_needed": subscription.api_endpoints_needed
    }
    
    return subscription


@configure_multivendor_network.step("Test API Connectivity")
async def test_api_connectivity(subscription: MultiVendorConfigurationProvisioning) -> State:
    """Test connectivity to all required API endpoints and devices"""
    
    api_status = {}
    connectivity_results = {}
    
    # Test API endpoints
    for endpoint_name in subscription.api_endpoints_needed:
        try:
            status = api_manager.validate_endpoint_connectivity(endpoint_name)
            api_status[endpoint_name] = status
        except Exception as e:
            api_status[endpoint_name] = {
                "status": "error",
                "message": str(e)
            }
    
    # Test device connectivity if requested
    if subscription.test_connectivity_first:
        connectivity_tasks = []
        
        for device_info in subscription.device_info:
            if "error" not in device_info:
                task = device_connection_manager.test_device_connectivity(device_info["device_id"])
                connectivity_tasks.append((device_info["device_id"], task))
        
        # Execute connectivity tests concurrently
        for device_id, task in connectivity_tasks:
            try:
                test_results = await task
                connectivity_results[device_id] = test_results
            except Exception as e:
                connectivity_results[device_id] = {"error": str(e)}
    
    subscription.api_endpoint_status = api_status
    subscription.connectivity_tests = connectivity_results
    
    return subscription


@configure_multivendor_network.step("Deploy Multi-Vendor Configurations")
async def deploy_configurations(subscription: MultiVendorConfigurationProvisioning) -> State:
    """Deploy configuration to all devices using optimal connection methods"""
    
    deployment_results = []
    deployment_tasks = []
    
    for device_info in subscription.device_info:
        if "error" in device_info:
            deployment_results.append({
                "device_id": device_info["device_id"],
                "success": False,
                "error": device_info["error"]
            })
            continue
        
        device_id = device_info["device_id"]
        
        try:
            # Generate platform-specific configuration
            config = generate_platform_specific_configuration(
                subscription.configuration_type,
                device_info["platform"],
                {
                    "interface_name": subscription.interface_name,
                    "interface_description": subscription.interface_description,
                    "interface_vlan": subscription.interface_vlan,
                    "vlan_id": subscription.vlan_id,
                    "vlan_name": subscription.vlan_name,
                    "custom_config": subscription.custom_config
                }
            )
            
            if not config:
                deployment_results.append({
                    "device_id": device_id,
                    "success": False,
                    "error": f"No configuration generated for platform {device_info['platform']}"
                })
                continue
            
            # Create deployment task
            task = deploy_device_configuration(
                device_id,
                config,
                backup_before_change=subscription.backup_before_change
            )
            deployment_tasks.append((device_id, device_info, task))
            
        except Exception as e:
            deployment_results.append({
                "device_id": device_id,
                "success": False,
                "error": str(e)
            })
    
    # Execute deployments concurrently (with some rate limiting)
    batch_size = 5  # Deploy to 5 devices at a time
    for i in range(0, len(deployment_tasks), batch_size):
        batch = deployment_tasks[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[task for _, _, task in batch],
            return_exceptions=True
        )
        
        for (device_id, device_info, _), result in zip(batch, batch_results):
            if isinstance(result, Exception):
                deployment_results.append({
                    "device_id": device_id,
                    "device_name": device_info["name"],
                    "manufacturer": device_info["manufacturer"],
                    "platform": device_info["platform"],
                    "connection_method": device_info["connection_method"],
                    "api_endpoint": device_info.get("api_endpoint"),
                    "success": False,
                    "error": str(result)
                })
            else:
                deployment_results.append({
                    "device_id": device_id,
                    "device_name": device_info["name"],
                    "manufacturer": device_info["manufacturer"],
                    "platform": device_info["platform"],
                    "connection_method": device_info["connection_method"],
                    "api_endpoint": device_info.get("api_endpoint"),
                    "success": result.success,
                    "deployment_method": result.method,
                    "message": result.message
                })
    
    subscription.deployment_results = deployment_results
    
    # Generate deployment statistics
    subscription.deployment_statistics = {
        "total_deployments": len(deployment_results),
        "successful_deployments": len([r for r in deployment_results if r["success"]]),
        "failed_deployments": len([r for r in deployment_results if not r["success"]]),
        "cisco_success": len([r for r in deployment_results if r.get("manufacturer") == "cisco" and r["success"]]),
        "juniper_success": len([r for r in deployment_results if r.get("manufacturer") == "juniper" and r["success"]]),
        "arista_success": len([r for r in deployment_results if r.get("manufacturer") == "arista" and r["success"]]),
        "centralized_api_deployments": len([r for r in deployment_results if "Centralized API" in r.get("connection_method", "")]),
        "direct_ssh_deployments": len([r for r in deployment_results if "Direct SSH" in r.get("connection_method", "")])
    }
    
    return subscription


@configure_multivendor_network.step("Validate Deployment Results")
async def validate_deployment(subscription: MultiVendorConfigurationProvisioning) -> State:
    """Validate configuration deployment across all devices"""
    
    if not subscription.validate_after_deployment:
        return subscription
    
    validation_results = []
    validation_tasks = []
    
    # Create validation tasks for successful deployments
    for result in subscription.deployment_results:
        if result["success"]:
            device_id = result["device_id"]
            
            # Generate validation command based on configuration type
            validation_command = generate_validation_command(
                subscription.configuration_type,
                result["platform"]
            )
            
            if validation_command:
                task = execute_device_command(device_id, validation_command)
                validation_tasks.append((device_id, result, task))
    
    # Execute validation commands
    for device_id, device_result, task in validation_tasks:
        try:
            validation_result = await task
            
            validation_results.append({
                "device_id": device_id,
                "device_name": device_result["device_name"],
                "validation_success": validation_result.success,
                "validation_output": validation_result.data.get("output") if validation_result.data else None,
                "validation_method": validation_result.method
            })
            
        except Exception as e:
            validation_results.append({
                "device_id": device_id,
                "validation_success": False,
                "error": str(e)
            })
    
    subscription.validation_results = validation_results
    
    return subscription


# Helper Functions

def get_all_network_devices_from_netbox() -> List[tuple]:
    """Get all network devices from NetBox with platform information"""
    try:
        devices = netbox.get_devices(status="active")
        device_options = []
        
        for device in devices:
            # Filter network devices
            device_role = device.get("device_role", {}).get("slug", "")
            if any(role in device_role for role in ["router", "switch", "firewall", "access-point"]):
                manufacturer = device.get("device_type", {}).get("manufacturer", {}).get("slug", "unknown")
                platform = device.get("platform", {}).get("slug", "unknown")
                site = device.get("site", {}).get("name", "unknown")
                
                display_name = f"{device['name']} ({manufacturer}-{platform} @ {site})"
                device_options.append((str(device["id"]), display_name))
        
        return device_options if device_options else [("manual", "Manual Device Entry")]
    except:
        return [("manual", "Manual Device Entry")]


def generate_platform_specific_configuration(config_type: str, platform: str, params: Dict[str, Any]) -> Optional[str]:
    """Generate platform-specific configuration"""
    
    if config_type == "interface_config" and params.get("interface_name"):
        return generate_interface_config(platform, params)
    elif config_type == "vlan_config" and params.get("vlan_id"):
        return generate_vlan_config(platform, params)
    elif config_type == "custom_config" and params.get("custom_config"):
        return params["custom_config"]
    
    return None


def generate_interface_config(platform: str, params: Dict[str, Any]) -> str:
    """Generate interface configuration for different platforms"""
    
    interface_name = params["interface_name"]
    description = params.get("interface_description", "Configured by Orchestrator")
    vlan = params.get("interface_vlan")
    
    if platform in ["ios", "iosxe", "nxos"]:
        # Cisco configuration
        config = f"""interface {interface_name}
 description {description}
 no shutdown"""
        if vlan:
            config += f"\n switchport access vlan {vlan}"
        return config
        
    elif platform == "eos":
        # Arista configuration
        config = f"""interface {interface_name}
   description {description}
   no shutdown"""
        if vlan:
            config += f"\n   switchport access vlan {vlan}"
        return config
        
    elif platform == "junos":
        # Juniper configuration
        config = f"""set interfaces {interface_name} description "{description}\""""
        if vlan:
            config += f"\nset interfaces {interface_name} unit 0 family ethernet-switching vlan members {vlan}"
        return config
    
    return None


def generate_vlan_config(platform: str, params: Dict[str, Any]) -> str:
    """Generate VLAN configuration for different platforms"""
    
    vlan_id = params["vlan_id"]
    vlan_name = params.get("vlan_name", f"VLAN_{vlan_id}")
    
    if platform in ["ios", "iosxe", "nxos"]:
        return f"""vlan {vlan_id}
 name {vlan_name}"""
        
    elif platform == "eos":
        return f"""vlan {vlan_id}
   name {vlan_name}"""
        
    elif platform == "junos":
        return f"""set vlans {vlan_name} vlan-id {vlan_id}"""
    
    return None


def generate_validation_command(config_type: str, platform: str) -> Optional[str]:
    """Generate validation command for different platforms"""
    
    if config_type == "interface_config":
        if platform in ["ios", "iosxe", "nxos"]:
            return "show interfaces status"
        elif platform == "eos":
            return "show interfaces status"
        elif platform == "junos":
            return "show interfaces terse"
            
    elif config_type == "vlan_config":
        if platform in ["ios", "iosxe", "nxos"]:
            return "show vlan brief"
        elif platform == "eos":
            return "show vlan"
        elif platform == "junos":
            return "show vlans"
    
    return "show version"  # Default validation command
