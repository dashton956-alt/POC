"""
BGP Configuration Workflow  
Implements comprehensive BGP routing protocol configuration
Uses centralized API management with NetBox integration for optimal device connectivity
"""

from orchestrator import workflow
from orchestrator.forms import FormPage
from orchestrator.targets import Target
from orchestrator.types import State, SubscriptionLifecycle, UUIDstr
from orchestrator.workflow import Step, StepList, begin, done
from orchestrator.workflows.steps import store_process_subscription
from pydantic import Field, validator
from pydantic_forms.core import FormPage
from pydantic_forms.types import Choice
from typing import List, Dict, Any, Optional
import asyncio

from products.product_types.routing import RoutingInactive, RoutingProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from services.api_manager import api_manager, get_device_connection
from services.device_connector import device_connection_manager, connect_to_device, deploy_device_configuration
from workflows.shared import device_selector

def bgp_configuration_form_generator() -> FormPage:
    """Generate BGP configuration form with NetBox-driven options"""
    
    # Get devices that support BGP from NetBox
    all_devices = netbox.get_devices(status="active", role__in=["router", "switch", "firewall"])
    device_options = []
    
    # Filter devices by platform capability and add context
    for device in all_devices:
        if device.get("platform"):
            platform = device["platform"]["slug"]
            # Only include devices with BGP-capable platforms
            if platform in ["ios", "eos", "nxos", "junos", "iosxr"]:
                manufacturer = device.get("device_type", {}).get("manufacturer", {}).get("slug", "unknown")
                site = device.get("site", {}).get("name", "unknown-site")
                device_options.append((
                    device["id"], 
                    f"{device['name']} ({manufacturer} - {platform} @ {site})"
                ))
    
    # Get ASN ranges from NetBox IPAM or use common ranges
    asn_ranges = get_asn_ranges_from_netbox()
    
    # Get existing BGP peers from NetBox for reference
    existing_peers = get_bgp_peers_from_netbox()
    
    # Get sites for neighbor grouping
    sites = netbox.get_sites()
    site_options = [(site["slug"], site["name"]) for site in sites]g protocol configuration across multiple device platforms

Features:
- BGP neighbor configuration
- Route policy and filtering
- Multi-homing and redundancy
- AS path manipulation  
- Route summarization
- Multi-platform support (Cisco IOS/NX-OS, Arista EOS, Juniper)
"""

from orchestrator.forms import FormPage, MultiForm, ReadOnlyField, get_form_options
from orchestrator.targets import Target
from orchestrator.types import State, UUIDstr
from orchestrator.workflow import StepList, begin, step
from orchestrator.workflows import LazyWorkflowInstance
from pydantic import Field
from typing import List, Dict, Optional, Any
import ipaddress

from utils.netbox import netbox
from utils.ansible_runner import ansible


class BGPConfigurationBase:
    """Base BGP configuration model"""
    bgp_deployment_name: str = Field(..., description="BGP deployment name")
    local_asn: int = Field(..., description="Local BGP AS number")
    router_id: Optional[str] = Field(None, description="BGP router ID")
    target_devices: List[str] = Field(..., description="Target device IDs")
    
    # BGP Neighbors
    bgp_neighbors: List[Dict] = Field(default_factory=list, description="BGP neighbor configurations")
    
    # Route Policies
    inbound_route_policies: List[Dict] = Field(default_factory=list, description="Inbound route policies")
    outbound_route_policies: List[Dict] = Field(default_factory=list, description="Outbound route policies")
    
    # Advanced BGP Features
    enable_bgp_confederation: bool = Field(False, description="Enable BGP confederation")
    confederation_id: Optional[int] = Field(None, description="BGP confederation ID")
    enable_route_reflector: bool = Field(False, description="Enable route reflector")
    route_reflector_cluster_id: Optional[str] = Field(None, description="Route reflector cluster ID")
    
    # Configuration Options
    backup_current_config: bool = Field(True, description="Backup current BGP configuration")
    validate_deployment: bool = Field(True, description="Validate BGP deployment")


class BGPConfigurationProvisioning(BGPConfigurationBase):
    """BGP configuration provisioning model with deployment results"""
    
    # Device configurations (populated during workflow)
    device_configurations: Dict[str, Any] = Field(default_factory=dict)
    configuration_backups: Dict[str, str] = Field(default_factory=dict)
    bgp_deployment_results: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    neighbor_status: Dict[str, Any] = Field(default_factory=dict)


def bgp_configuration_form_generator() -> FormPage:
    """Generate BGP configuration form"""
    
    # Get available devices that support BGP
    devices = netbox.get_devices(platform__in=["ios", "eos", "nxos", "junos"])
    device_options = [(d["id"], f"{d['name']} ({d['platform']['slug']})") for d in devices]
    
    return FormPage(
        name="BGP Configuration",
        target_description="Configure BGP routing protocol with neighbor relationships and route policies",
        form_group=[
            # Basic BGP Configuration
            MultiForm(
                name="bgp_basic",
                label="Basic BGP Configuration",
                fields=[
                    Field("bgp_deployment_name", str, description="BGP deployment name (e.g., 'WAN-BGP-Deployment')"),
                    Field("local_asn", int, description="Local BGP AS number (1-4294967295)"),
                    Field("router_id", Optional[str], description="BGP router ID (leave blank for auto-assignment)"),
                    Field("target_devices", List[str], description="Target devices for BGP configuration", options=device_options),
                ]
            ),
            
            # BGP Neighbors
            MultiForm(
                name="neighbors",
                label="BGP Neighbors",
                fields=[
                    Field("neighbor_discovery_method", str, description="Neighbor discovery method", 
                          options=[("manual", "Manual Entry"), ("netbox_peers", "From NetBox Peers"), ("site_based", "Site-based Auto-discovery")]),
                    Field("peer_site_filter", str, description="Filter peers by site (if using site-based)", options=site_options, default=""),
                    Field("neighbor_ip_1", str, description="Neighbor 1 IP address", default=""),
                    Field("neighbor_asn_1", int, description="Neighbor 1 AS number", default=0),
                    Field("neighbor_description_1", str, description="Neighbor 1 description", default=""),
                    Field("neighbor_ip_2", str, description="Neighbor 2 IP address", default=""),
                    Field("neighbor_asn_2", int, description="Neighbor 2 AS number", default=0),
                    Field("neighbor_description_2", str, description="Neighbor 2 description", default=""),
                    Field("auto_configure_existing_peers", bool, description="Auto-configure existing NetBox BGP peers", default=False),
                ]
            ),
            
            # Route Policies
            MultiForm(
                name="route_policies",
                label="Route Policies",
                fields=[
                    Field("route_policy_source", str, description="Route policy source", 
                          options=[("netbox_prefixes", "From NetBox Prefixes"), ("manual", "Manual Entry")]),
                    Field("advertise_connected", bool, description="Advertise connected networks", default=True),
                    Field("advertise_static", bool, description="Advertise static routes", default=False),
                    Field("network_filter_site", str, description="Filter networks by site", options=site_options, default=""),
                    Field("enable_default_route", bool, description="Advertise default route", default=False),
                    Field("network_advertisement_1", str, description="Manual network 1 (CIDR)", default=""),
                    Field("network_advertisement_2", str, description="Manual network 2 (CIDR)", default=""),
                    Field("enable_route_aggregation", bool, description="Enable automatic route aggregation", default=True),
                ]
            ),
            
            # Advanced BGP Features
            MultiForm(
                name="advanced_bgp",
                label="Advanced BGP Features",
                fields=[
                    Field("enable_bgp_confederation", bool, description="Enable BGP confederation", default=False),
                    Field("confederation_id", Optional[int], description="BGP confederation ID"),
                    Field("enable_route_reflector", bool, description="Enable route reflector", default=False),
                    Field("route_reflector_cluster_id", Optional[str], description="Route reflector cluster ID"),
                    Field("enable_graceful_restart", bool, description="Enable BGP graceful restart", default=True),
                    Field("bgp_timers_keepalive", int, description="BGP keepalive timer (seconds)", default=60),
                    Field("bgp_timers_hold", int, description="BGP hold timer (seconds)", default=180),
                ]
            ),
            
            # Configuration Options  
            MultiForm(
                name="config_options",
                label="Configuration Options",
                fields=[
                    Field("backup_current_config", bool, description="Backup current BGP configuration", default=True),
                    Field("validate_deployment", bool, description="Validate BGP deployment", default=True),
                    Field("enable_bgp_logging", bool, description="Enable BGP logging", default=True),
                    Field("rollback_on_failure", bool, description="Auto-rollback on failure", default=True),
                ]
            )
        ]
    )


@step("Configure BGP Protocol")
def configure_bgp_protocol_start(
    bgp_deployment_name: str,
    local_asn: int,
    router_id: Optional[str],
    target_devices: List[str],
    neighbor_ip_1: str,
    neighbor_asn_1: int,
    neighbor_description_1: str,
    neighbor_ip_2: str,
    neighbor_asn_2: int,
    neighbor_description_2: str,
    neighbor_ip_3: str,
    neighbor_asn_3: int,
    neighbor_description_3: str,
    enable_default_route: bool,
    network_advertisement_1: str,
    network_advertisement_2: str,
    network_advertisement_3: str,
    enable_route_summarization: bool,
    summary_address: str,
    enable_bgp_confederation: bool,
    confederation_id: Optional[int],
    enable_route_reflector: bool,
    route_reflector_cluster_id: Optional[str],
    enable_graceful_restart: bool,
    bgp_timers_keepalive: int,
    bgp_timers_hold: int,
    backup_current_config: bool,
    validate_deployment: bool,
    enable_bgp_logging: bool,
    rollback_on_failure: bool
) -> State:
    """Initialize BGP configuration with form data"""
    
    # Build BGP neighbors list
    bgp_neighbors = []
    for i in [1, 2, 3]:
        neighbor_ip = locals()[f"neighbor_ip_{i}"]
        neighbor_asn = locals()[f"neighbor_asn_{i}"]
        neighbor_desc = locals()[f"neighbor_description_{i}"]
        
        if neighbor_ip and neighbor_asn:
            bgp_neighbors.append({
                "ip_address": neighbor_ip,
                "remote_asn": neighbor_asn,
                "description": neighbor_desc or f"BGP-Neighbor-{i}",
                "timers_keepalive": bgp_timers_keepalive,
                "timers_hold": bgp_timers_hold,
                "graceful_restart": enable_graceful_restart
            })
    
    # Build route policies
    inbound_route_policies = []
    outbound_route_policies = []
    
    # Network advertisements
    networks_to_advertise = []
    for i in [1, 2, 3]:
        network = locals()[f"network_advertisement_{i}"]
        if network:
            networks_to_advertise.append(network)
    
    if networks_to_advertise:
        outbound_route_policies.append({
            "type": "network_advertisement",
            "networks": networks_to_advertise
        })
    
    if enable_default_route:
        outbound_route_policies.append({
            "type": "default_route",
            "enabled": True
        })
    
    if enable_route_summarization and summary_address:
        outbound_route_policies.append({
            "type": "route_summarization", 
            "summary_address": summary_address
        })
    
    return {
        "subscription": BGPConfigurationProvisioning(
            bgp_deployment_name=bgp_deployment_name,
            local_asn=local_asn,
            router_id=router_id,
            target_devices=target_devices,
            bgp_neighbors=bgp_neighbors,
            inbound_route_policies=inbound_route_policies,
            outbound_route_policies=outbound_route_policies,
            enable_bgp_confederation=enable_bgp_confederation,
            confederation_id=confederation_id,
            enable_route_reflector=enable_route_reflector,
            route_reflector_cluster_id=route_reflector_cluster_id,
            backup_current_config=backup_current_config,
            validate_deployment=validate_deployment
        )
    }


configure_bgp_protocol = begin >> configure_bgp_protocol_start


@configure_bgp_protocol.step("Validate Devices and BGP Configuration")
def validate_bgp_configuration(subscription: BGPConfigurationProvisioning) -> State:
    """Validate target devices and BGP configuration parameters"""
    
    validated_devices = []
    bgp_validation = {}
    
    # Validate ASN
    if not (1 <= subscription.local_asn <= 4294967295):
        raise ValueError(f"Invalid BGP ASN: {subscription.local_asn}. Must be between 1 and 4294967295")
    
    # Validate each target device
    for device_id in subscription.target_devices:
        device_info = netbox.get_device(device_id)
        if not device_info:
            raise ValueError(f"Device {device_id} not found in NetBox")
        
        platform = device_info.get("platform", {}).get("slug")
        device_name = device_info.get("name")
        
        # Validate BGP support
        bgp_supported_platforms = ["ios", "eos", "nxos", "junos", "iosxr"]
        if platform not in bgp_supported_platforms:
            raise ValueError(f"Device {device_name} platform '{platform}' does not support BGP")
        
        # Get device management IP
        management_ip = device_info.get("primary_ip4", {}).get("address", "").split("/")[0]
        if not management_ip:
            raise ValueError(f"Device {device_name} has no primary IP address")
        
        # Generate router ID if not provided
        if not subscription.router_id:
            subscription.router_id = management_ip
        
        validated_devices.append({
            "device_id": device_id,
            "device_name": device_name,
            "platform": platform,
            "management_ip": management_ip,
            "router_id": subscription.router_id
        })
    
    # Validate BGP neighbors
    for neighbor in subscription.bgp_neighbors:
        try:
            ipaddress.ip_address(neighbor["ip_address"])
        except ValueError:
            raise ValueError(f"Invalid neighbor IP address: {neighbor['ip_address']}")
        
        if not (1 <= neighbor["remote_asn"] <= 4294967295):
            raise ValueError(f"Invalid neighbor ASN: {neighbor['remote_asn']}")
    
    # Validate network advertisements
    for policy in subscription.outbound_route_policies:
        if policy["type"] == "network_advertisement":
            for network in policy["networks"]:
                try:
                    ipaddress.ip_network(network)
                except ValueError:
                    raise ValueError(f"Invalid network for advertisement: {network}")
    
    subscription.device_configurations = {d["device_id"]: d for d in validated_devices}
    subscription.validation_results["configuration_validation"] = bgp_validation
    
    return {"subscription": subscription}


@configure_bgp_protocol.step("Deploy BGP Configuration via Optimal API")
async def deploy_bgp_config_optimal_api(subscription: BGPConfigurationProvisioning) -> State:
    """Deploy BGP configuration using optimal connection method"""
    
    deployment_results = []
    
    for device_config in subscription.device_configurations.values():
        device_id = device_config["device_id"]
        
        try:
            # Get optimal connection information
            connection_info = get_device_connection(device_id)
            
            # Log connection method being used
            connection_method = "Centralized API" if connection_info["use_centralized_api"] else "Direct SSH"
            api_endpoint = connection_info.get("api_endpoint", "N/A")
            device_ip = connection_info.get("device_ip", "Unknown")
            
            print(f"Deploying BGP to {device_id} ({device_ip}) via {connection_method}")
            if connection_info["use_centralized_api"]:
                print(f"  Using API endpoint: {api_endpoint}")
            
            # Generate BGP configuration based on device platform
            bgp_config = generate_bgp_configuration(
                device_config,
                subscription.local_as,
                subscription.router_id,
                subscription.bgp_neighbors,
                subscription.inbound_route_policies,
                subscription.outbound_route_policies
            )
            
            # Deploy configuration using optimal method
            deployment_result = await deploy_device_configuration(
                device_id,
                bgp_config,
                template_name=f"BGP-AS{subscription.local_as}",
                backup_before_change=subscription.backup_current_config
            )
            
            # Store deployment results
            deployment_results.append({
                "device_id": device_id,
                "device_ip": device_ip,
                "connection_method": connection_method,
                "api_endpoint": api_endpoint,
                "success": deployment_result.success,
                "deployment_method": deployment_result.method,
                "message": deployment_result.message,
                "config_lines": len(bgp_config.split('\n')) if bgp_config else 0
            })
            
            if not deployment_result.success:
                print(f"BGP deployment failed for {device_id}: {deployment_result.message}")
            else:
                print(f"BGP deployed successfully to {device_id} via {deployment_result.method}")
                
        except Exception as e:
            deployment_results.append({
                "device_id": device_id,
                "success": False,
                "error": str(e),
                "connection_method": "Error",
                "api_endpoint": "N/A"
            })
            print(f"Error deploying BGP to {device_id}: {e}")
    
    # Store results in subscription
    subscription.deployment_results = deployment_results
    subscription.successful_deployments = len([r for r in deployment_results if r["success"]])
    subscription.failed_deployments = len([r for r in deployment_results if not r["success"]])
    
    # Generate deployment summary
    subscription.deployment_summary = {
        "total_devices": len(deployment_results),
        "successful": subscription.successful_deployments,
        "failed": subscription.failed_deployments,
        "centralized_api_used": len([r for r in deployment_results if "Centralized API" in r.get("connection_method", "")]),
        "direct_ssh_used": len([r for r in deployment_results if "Direct SSH" in r.get("connection_method", "")]),
        "api_endpoints_used": list(set([r.get("api_endpoint") for r in deployment_results if r.get("api_endpoint") != "N/A"]))
    }
    
    return {"subscription": subscription}


@configure_bgp_protocol.step("Test BGP Connectivity Methods")
async def test_bgp_connectivity_methods(subscription: BGPConfigurationProvisioning) -> State:
    """Test all available connectivity methods for BGP devices"""
    
    connectivity_tests = []
    
    for device_config in subscription.device_configurations.values():
        device_id = device_config["device_id"]
        
        try:
            # Test all connectivity methods for this device
            test_results = await device_connection_manager.test_device_connectivity(device_id)
            
            connectivity_tests.append({
                "device_id": device_id,
                "device_name": device_config.get("name", f"Device-{device_id}"),
                "test_results": test_results,
                "optimal_method": "centralized_api" if any(r["success"] for k, r in test_results.items() if k != "direct_ssh") else "direct_ssh"
            })
            
        except Exception as e:
            connectivity_tests.append({
                "device_id": device_id,
                "error": str(e),
                "test_results": {},
                "optimal_method": "unknown"
            })
    
    subscription.connectivity_tests = connectivity_tests
    
    return {"subscription": subscription}


@configure_bgp_protocol.step("Backup Current BGP Configuration")
def backup_current_bgp_config(subscription: BGPConfigurationProvisioning) -> State:
    """Backup current BGP configuration"""
    
    if not subscription.backup_current_config:
        return {"subscription": subscription}
    
    backup_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        try:
            # Run BGP backup playbook
            backup_result = ansible.run_playbook(
                "backup_bgp_configuration.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "backup_location": f"/tmp/bgp_backup_{device_name}_{subscription.bgp_deployment_name}"
                }
            )
            
            backup_results[device_id] = {
                "status": "success" if backup_result["rc"] == 0 else "failed",
                "backup_file": f"/tmp/bgp_backup_{device_name}_{subscription.bgp_deployment_name}.cfg" if backup_result["rc"] == 0 else None,
                "error": backup_result.get("stderr") if backup_result["rc"] != 0 else None
            }
            
        except Exception as e:
            backup_results[device_id] = {
                "status": "error",
                "error": str(e)
            }
    
    subscription.configuration_backups = backup_results
    return {"subscription": subscription}


@configure_bgp_protocol.step("Configure BGP Process")
def configure_bgp_process(subscription: BGPConfigurationProvisioning) -> State:
    """Configure BGP routing process on each device"""
    
    bgp_deployment_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        try:
            # Generate platform-specific BGP configuration
            bgp_config = generate_bgp_configuration(
                platform=platform,
                local_asn=subscription.local_asn,
                router_id=subscription.router_id,
                neighbors=subscription.bgp_neighbors,
                inbound_policies=subscription.inbound_route_policies,
                outbound_policies=subscription.outbound_route_policies,
                confederation_enabled=subscription.enable_bgp_confederation,
                confederation_id=subscription.confederation_id,
                route_reflector_enabled=subscription.enable_route_reflector,
                route_reflector_cluster_id=subscription.route_reflector_cluster_id
            )
            
            # Deploy BGP configuration
            deploy_result = ansible.run_playbook(
                "deploy_bgp_configuration.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "local_asn": subscription.local_asn,
                    "bgp_configuration": bgp_config,
                    "deployment_name": subscription.bgp_deployment_name,
                    "validate_config": subscription.validate_deployment
                }
            )
            
            bgp_deployment_results[device_id] = {
                "status": "success" if deploy_result["rc"] == 0 else "failed",
                "bgp_configured": deploy_result["rc"] == 0,
                "config_lines": len(bgp_config.split('\n')) if bgp_config else 0,
                "deployment_time": deploy_result.get("end"),
                "error": deploy_result.get("stderr") if deploy_result["rc"] != 0 else None
            }
            
        except Exception as e:
            bgp_deployment_results[device_id] = {
                "status": "error",
                "bgp_configured": False,
                "error": str(e)
            }
    
    subscription.bgp_deployment_results = bgp_deployment_results
    return {"subscription": subscription}


@configure_bgp_protocol.step("Validate BGP Neighbor Establishment")
def validate_bgp_neighbors(subscription: BGPConfigurationProvisioning) -> State:
    """Validate BGP neighbor relationships are established"""
    
    if not subscription.validate_deployment:
        return {"subscription": subscription}
    
    neighbor_validation_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        try:
            # Validate BGP neighbors
            validation_result = ansible.run_playbook(
                "validate_bgp_neighbors.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "local_asn": subscription.local_asn,
                    "expected_neighbors": [n["ip_address"] for n in subscription.bgp_neighbors],
                    "deployment_name": subscription.bgp_deployment_name
                }
            )
            
            neighbor_validation_results[device_id] = {
                "status": "passed" if validation_result["rc"] == 0 else "failed",
                "neighbors_established": validation_result["rc"] == 0,
                "neighbor_count": len(subscription.bgp_neighbors),
                "error": validation_result.get("stderr") if validation_result["rc"] != 0 else None
            }
            
        except Exception as e:
            neighbor_validation_results[device_id] = {
                "status": "error",
                "neighbors_established": False,
                "error": str(e)
            }
    
    subscription.neighbor_status = neighbor_validation_results
    return {"subscription": subscription}


@configure_bgp_protocol.step("Update NetBox with BGP Information")
def update_netbox_bgp_info(subscription: BGPConfigurationProvisioning) -> State:
    """Update NetBox with BGP configuration information"""
    
    netbox_updates = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        deployment_status = subscription.bgp_deployment_results[device_id]
        
        if deployment_status["status"] == "success":
            # Update device custom fields with BGP information
            update_result = netbox.update_device(device_id, {
                "custom_fields": {
                    "bgp_asn": subscription.local_asn,
                    "bgp_router_id": subscription.router_id,
                    "bgp_deployment": subscription.bgp_deployment_name,
                    "bgp_neighbor_count": len(subscription.bgp_neighbors),
                    "bgp_status": "configured",
                    "bgp_last_updated": deployment_status["deployment_time"]
                }
            })
            
            netbox_updates[device_id] = {
                "status": "updated" if update_result else "failed",
                "device_name": device_name
            }
        else:
            netbox_updates[device_id] = {
                "status": "skipped",
                "reason": "deployment_failed",
                "device_name": device_name
            }
    
    subscription.validation_results["netbox_updates"] = netbox_updates
    return {"subscription": subscription}


# Helper Functions

def generate_bgp_configuration(platform: str, local_asn: int, router_id: str, neighbors: List[Dict],
                              inbound_policies: List[Dict], outbound_policies: List[Dict],
                              confederation_enabled: bool = False, confederation_id: Optional[int] = None,
                              route_reflector_enabled: bool = False, route_reflector_cluster_id: Optional[str] = None) -> str:
    """Generate platform-specific BGP configuration"""
    
    if platform == "ios":
        return generate_ios_bgp_config(local_asn, router_id, neighbors, inbound_policies, outbound_policies, 
                                      confederation_enabled, confederation_id, route_reflector_enabled, route_reflector_cluster_id)
    elif platform == "eos":
        return generate_eos_bgp_config(local_asn, router_id, neighbors, inbound_policies, outbound_policies,
                                      confederation_enabled, confederation_id, route_reflector_enabled, route_reflector_cluster_id)
    elif platform == "nxos":
        return generate_nxos_bgp_config(local_asn, router_id, neighbors, inbound_policies, outbound_policies,
                                       confederation_enabled, confederation_id, route_reflector_enabled, route_reflector_cluster_id)
    elif platform == "junos":
        return generate_junos_bgp_config(local_asn, router_id, neighbors, inbound_policies, outbound_policies,
                                        confederation_enabled, confederation_id, route_reflector_enabled, route_reflector_cluster_id)
    else:
        raise ValueError(f"Unsupported platform for BGP configuration: {platform}")


def generate_ios_bgp_config(local_asn: int, router_id: str, neighbors: List[Dict],
                           inbound_policies: List[Dict], outbound_policies: List[Dict],
                           confederation_enabled: bool, confederation_id: Optional[int],
                           route_reflector_enabled: bool, route_reflector_cluster_id: Optional[str]) -> str:
    """Generate Cisco IOS BGP configuration"""
    
    config_lines = []
    
    # BGP process
    config_lines.extend([
        f"router bgp {local_asn}",
        f" bgp router-id {router_id}",
        " bgp log-neighbor-changes",
        " no bgp default ipv4-unicast"
    ])
    
    # BGP confederation
    if confederation_enabled and confederation_id:
        config_lines.extend([
            f" bgp confederation identifier {confederation_id}",
            f" bgp confederation peers {local_asn}"
        ])
    
    # Route reflector
    if route_reflector_enabled:
        if route_reflector_cluster_id:
            config_lines.append(f" bgp cluster-id {route_reflector_cluster_id}")
    
    # BGP neighbors
    for neighbor in neighbors:
        config_lines.extend([
            f" neighbor {neighbor['ip_address']} remote-as {neighbor['remote_asn']}",
            f" neighbor {neighbor['ip_address']} description {neighbor['description']}",
            f" neighbor {neighbor['ip_address']} timers {neighbor['timers_keepalive']} {neighbor['timers_hold']}"
        ])
        
        if neighbor.get("graceful_restart"):
            config_lines.append(f" neighbor {neighbor['ip_address']} graceful-restart")
    
    # Address family IPv4
    config_lines.extend([
        " !",
        " address-family ipv4"
    ])
    
    # Network advertisements
    for policy in outbound_policies:
        if policy["type"] == "network_advertisement":
            for network in policy["networks"]:
                config_lines.append(f"  network {network}")
        elif policy["type"] == "default_route":
            config_lines.append("  default-information originate")
        elif policy["type"] == "route_summarization":
            config_lines.append(f"  aggregate-address {policy['summary_address']}")
    
    # Activate neighbors for IPv4
    for neighbor in neighbors:
        config_lines.extend([
            f"  neighbor {neighbor['ip_address']} activate"
        ])
        
        if route_reflector_enabled:
            config_lines.append(f"  neighbor {neighbor['ip_address']} route-reflector-client")
    
    config_lines.extend([
        " exit-address-family",
        "!"
    ])
    
    return "\n".join(config_lines)


def generate_eos_bgp_config(local_asn: int, router_id: str, neighbors: List[Dict],
                           inbound_policies: List[Dict], outbound_policies: List[Dict],
                           confederation_enabled: bool, confederation_id: Optional[int],
                           route_reflector_enabled: bool, route_reflector_cluster_id: Optional[str]) -> str:
    """Generate Arista EOS BGP configuration"""
    
    config_lines = []
    
    # BGP process
    config_lines.extend([
        f"router bgp {local_asn}",
        f"   router-id {router_id}",
        "   bgp log-neighbor-changes"
    ])
    
    # BGP neighbors
    for neighbor in neighbors:
        config_lines.extend([
            f"   neighbor {neighbor['ip_address']} remote-as {neighbor['remote_asn']}",
            f"   neighbor {neighbor['ip_address']} description {neighbor['description']}",
            f"   neighbor {neighbor['ip_address']} timers {neighbor['timers_keepalive']} {neighbor['timers_hold']}"
        ])
    
    # Network advertisements
    for policy in outbound_policies:
        if policy["type"] == "network_advertisement":
            for network in policy["networks"]:
                config_lines.append(f"   network {network}")
        elif policy["type"] == "default_route":
            config_lines.append("   default-information originate")
        elif policy["type"] == "route_summarization":
            config_lines.append(f"   aggregate-address {policy['summary_address']}")
    
    # Route reflector
    if route_reflector_enabled:
        for neighbor in neighbors:
            config_lines.append(f"   neighbor {neighbor['ip_address']} route-reflector-client")
        if route_reflector_cluster_id:
            config_lines.append(f"   bgp cluster-id {route_reflector_cluster_id}")
    
    config_lines.append("!")
    
    return "\n".join(config_lines)


def generate_nxos_bgp_config(local_asn: int, router_id: str, neighbors: List[Dict],
                            inbound_policies: List[Dict], outbound_policies: List[Dict],
                            confederation_enabled: bool, confederation_id: Optional[int],
                            route_reflector_enabled: bool, route_reflector_cluster_id: Optional[str]) -> str:
    """Generate Cisco NX-OS BGP configuration"""
    
    config_lines = []
    
    # Enable BGP feature
    config_lines.extend([
        "feature bgp",
        f"router bgp {local_asn}",
        f"  router-id {router_id}",
        "  log-neighbor-changes"
    ])
    
    # BGP neighbors
    for neighbor in neighbors:
        config_lines.extend([
            f"  neighbor {neighbor['ip_address']} remote-as {neighbor['remote_asn']}",
            f"  neighbor {neighbor['ip_address']} description {neighbor['description']}",
            f"  neighbor {neighbor['ip_address']} timers {neighbor['timers_keepalive']} {neighbor['timers_hold']}"
        ])
    
    # Address family IPv4
    config_lines.extend([
        "  address-family ipv4 unicast"
    ])
    
    # Network advertisements
    for policy in outbound_policies:
        if policy["type"] == "network_advertisement":
            for network in policy["networks"]:
                config_lines.append(f"    network {network}")
        elif policy["type"] == "route_summarization":
            config_lines.append(f"    aggregate-address {policy['summary_address']}")
    
    # Activate neighbors
    for neighbor in neighbors:
        config_lines.append(f"    neighbor {neighbor['ip_address']} activate")
        
        if route_reflector_enabled:
            config_lines.append(f"    neighbor {neighbor['ip_address']} route-reflector-client")
    
    config_lines.append("!")
    
    return "\n".join(config_lines)


def generate_junos_bgp_config(local_asn: int, router_id: str, neighbors: List[Dict],
                             inbound_policies: List[Dict], outbound_policies: List[Dict],
                             confederation_enabled: bool, confederation_id: Optional[int],
                             route_reflector_enabled: bool, route_reflector_cluster_id: Optional[str]) -> str:
    """Generate Juniper JunOS BGP configuration"""
    
    config_lines = []
    
    # BGP configuration
    config_lines.extend([
        "protocols {",
        "    bgp {",
        f"        local-as {local_asn};",
        f"        router-id {router_id};"
    ])
    
    # Route reflector cluster
    if route_reflector_enabled and route_reflector_cluster_id:
        config_lines.append(f"        cluster {route_reflector_cluster_id};")
    
    # BGP groups and neighbors
    config_lines.append("        group external-peers {")
    config_lines.append("            type external;")
    
    for neighbor in neighbors:
        config_lines.extend([
            f"            neighbor {neighbor['ip_address']} {{",
            f"                description \"{neighbor['description']}\";",
            f"                peer-as {neighbor['remote_asn']};",
            f"                hold-time {neighbor['timers_hold']};",
            f"                keepalive {neighbor['timers_keepalive']};"
        ])
        
        if route_reflector_enabled:
            config_lines.append("                cluster;")
            
        config_lines.append("            }")
    
    config_lines.extend([
        "        }",
        "    }",
        "}"
    ])
    
    # Static routes for network advertisements
    if outbound_policies:
        config_lines.append("routing-options {")
        for policy in outbound_policies:
            if policy["type"] == "network_advertisement":
                for network in policy["networks"]:
                    config_lines.append(f"    static route {network} discard;")
        config_lines.append("}")
    
    return "\n".join(config_lines)


# NetBox Integration Helper Functions

def get_asn_ranges_from_netbox() -> List[tuple]:
    """Get ASN ranges from NetBox configuration"""
    try:
        # Try to get ASN ranges from NetBox custom config
        asn_ranges = netbox.get_custom_config("bgp_asn_ranges")
        if asn_ranges:
            return asn_ranges
    except:
        pass
    
    # Return common ASN ranges
    return [
        ("private", "Private ASNs (64512-65534)"),
        ("public", "Public ASNs"),
        ("4byte", "4-byte ASNs (4200000000+)")
    ]


def get_bgp_peers_from_netbox() -> List[Dict]:
    """Get existing BGP peers from NetBox"""
    try:
        # Look for devices with BGP role or custom field
        bgp_devices = netbox.get_devices(role="bgp-peer")
        peers = []
        
        for device in bgp_devices:
            if device.get("primary_ip4"):
                peers.append({
                    "ip_address": device["primary_ip4"]["address"].split("/")[0],
                    "name": device["name"],
                    "site": device.get("site", {}).get("name"),
                    "asn": device.get("custom_fields", {}).get("bgp_asn", 0)
                })
        
        return peers
    except:
        return []


def get_networks_from_netbox_site(site_slug: str) -> List[str]:
    """Get networks/prefixes from NetBox filtered by site"""
    try:
        prefixes = netbox.get_prefixes(site=site_slug, status="active")
        return [prefix["prefix"] for prefix in prefixes if not prefix.get("is_pool", False)]
    except:
        return []


def auto_discover_bgp_neighbors_by_site(target_devices: List[str], site_filter: str) -> List[Dict]:
    """Auto-discover potential BGP neighbors based on site topology"""
    neighbors = []
    
    try:
        # Get all devices in the specified site
        site_devices = netbox.get_devices(site=site_filter, status="active")
        
        for device in site_devices:
            # Skip if device is in target_devices (don't peer with self)
            if device["id"] in target_devices:
                continue
            
            # Look for devices that could be BGP peers
            device_role = device.get("device_role", {}).get("slug", "")
            if any(role in device_role for role in ["router", "firewall", "border", "edge"]):
                if device.get("primary_ip4"):
                    neighbors.append({
                        "ip_address": device["primary_ip4"]["address"].split("/")[0],
                        "remote_asn": device.get("custom_fields", {}).get("bgp_asn", 65001),  # Default ASN
                        "description": f"Auto-discovered-{device['name']}-{device['site']['name']}",
                        "auto_discovered": True
                    })
    except:
        pass
    
    return neighbors


def resolve_collector_ip(collector_selection: str, manual_ip: str) -> str:
    """Resolve collector IP from selection or manual entry"""
    if collector_selection == "manual":
        return manual_ip
    else:
        return collector_selection  # Already an IP address from NetBox device
