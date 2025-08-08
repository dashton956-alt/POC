"""
Configure OSPF Workflow
Deploy OSPF routing protocol with area design and optimization
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
from services.device_connector import device_connection_manager, connect_to_device, deploy_device_configuration, execute_device_command
from workflows.shared import device_selector


class OSPFConfigurationForm(FormPage):
    """OSPF Configuration Form"""
    
    # Target Devices - NetBox driven
    target_devices: List[str] = Field(
        description="Target Devices for OSPF",
        min_items=1,
        choices=get_ospf_capable_devices_from_netbox()
    )
    
    # Site Filter for Area Discovery
    site_filter: str = Field(
        description="Site for Area Auto-Discovery",
        choices=get_sites_from_netbox(),
        default=""
    )
    
    # OSPF Process Configuration
    ospf_process_id: int = Field(
        description="OSPF Process ID",
        ge=1,
        le=65535,
        default=1
    )
    
    router_id: Optional[str] = Field(
        description="Router ID (Optional - auto-generated from NetBox if not specified)",
        regex=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
        default=None
    )
    
    # Area Configuration - Enhanced with NetBox integration
    ospf_areas: List[Dict[str, Any]] = Field(
        description="OSPF Areas Configuration",
        min_items=1,
        default=get_default_ospf_areas_from_netbox()
    )
    
    # Network Configuration - NetBox prefix integration
    auto_discover_networks: bool = Field(
        description="Auto-discover networks from NetBox prefixes",
        default=True
    )
    
    networks: List[Dict[str, Any]] = Field(
        description="Networks to Advertise (auto-populated from NetBox)",
        min_items=0  # Allow empty if auto-discovery is enabled
    )
    
    # Authentication - NetBox security policy integration
    enable_authentication: bool = Field(
        description="Enable OSPF Authentication",
        default=get_ospf_auth_policy_from_netbox()
    )
    
    authentication_type: Choice = Field(
        description="Authentication Type",
        choices=get_supported_auth_types_from_netbox(),
        default="md5"
    )
    
    authentication_key: Optional[str] = Field(
        description="Authentication Key (from NetBox secrets if available)",
        min_length=8,
        max_length=64,
        default=None
    )
    
    # OSPF Features
    enable_area_summarization: bool = Field(
        description="Enable Area Summarization",
        default=True
    )
    
    default_route_advertisement: Choice = Field(
        description="Default Route Advertisement",
        choices=[
            ("none", "Don't Advertise"),
            ("always", "Always Advertise"),
            ("conditional", "Conditional Advertisement")
        ],
        default="none"
    )
    
    # Timers Configuration
    hello_interval: int = Field(
        description="Hello Interval (seconds)",
        ge=1,
        le=65535,
        default=10
    )
    
    dead_interval: int = Field(
        description="Dead Interval (seconds)",
        ge=1,
        le=65535,
        default=40
    )
    
    # Advanced Configuration
    enable_bfd: bool = Field(
        description="Enable BFD for Fast Convergence",
        default=False
    )
    
    max_lsa_count: int = Field(
        description="Maximum LSA Count",
        ge=1000,
        le=1000000,
        default=12000
    )
    
    reference_bandwidth: int = Field(
        description="Reference Bandwidth (Mbps)",
        ge=1,
        le=4294967,
        default=100000
    )
    
    # Route Filtering
    distribute_lists: List[Dict[str, Any]] = Field(
        description="Distribute Lists for Route Filtering",
        default=[]
    )
    
    @validator('authentication_key')
    def validate_auth_key(cls, v, values):
        if values.get('enable_authentication') and not v:
            raise ValueError("Authentication key is required when authentication is enabled")
        return v
    
    @validator('dead_interval')
    def validate_dead_interval(cls, v, values):
        hello = values.get('hello_interval', 10)
        if v <= hello:
            raise ValueError("Dead interval must be greater than hello interval")
        return v


@workflow("Configure OSPF", target=Target.CREATE)
def configure_ospf(subscription: RoutingInactive) -> State:
    """Configure OSPF routing protocol workflow"""
    return (
        begin
        >> store_process_subscription(subscription)
        >> validate_devices_and_networks
        >> design_ospf_topology
        >> generate_router_ids
        >> backup_current_routing_config
        >> configure_ospf_process
        >> configure_ospf_areas
        >> configure_ospf_interfaces
        >> configure_ospf_authentication
        >> configure_route_filtering
        >> verify_ospf_neighbors
        >> verify_ospf_database
        >> update_netbox_records
        >> done
    )


@configure_ospf.step("Validate Devices and Networks")
def validate_devices_and_networks(subscription: RoutingProvisioning) -> State:
    """Validate target devices and network configuration"""
    
    validated_devices = []
    network_validation = {}
    
    # Validate each target device
    for device_id in subscription.target_devices:
        device_info = netbox.get_device(device_id)
        if not device_info:
            raise ValueError(f"Device {device_id} not found in NetBox")
        
        # Check device capabilities
        device_platform = device_info.get("platform", {}).get("slug")
        device_vendor = device_info.get("device_type", {}).get("manufacturer", {}).get("slug")
        
        # Validate OSPF support
        ospf_supported_platforms = ["ios", "eos", "nxos", "junos", "iosxr"]
        if device_platform not in ospf_supported_platforms:
            raise ValueError(f"Device {device_info.get('name')} platform '{device_platform}' may not support OSPF")
        
        device_ip = device_info.get("primary_ip4", {}).get("address", "").split("/")[0]
        if not device_ip:
            raise ValueError(f"Device {device_info.get('name')} has no primary IP address")
        
        validated_devices.append({
            "device_id": device_id,
            "device_name": device_info.get("name"),
            "device_ip": device_ip,
            "platform": device_platform,
            "vendor": device_vendor,
            "interfaces": netbox.get_device_interfaces(device_id)
        })
    
    # Validate network configurations
    for network_config in subscription.networks:
        network_prefix = network_config.get("network")
        area_id = network_config.get("area_id", "0.0.0.0")
        
        # Validate network format
        import ipaddress
        try:
            network = ipaddress.ip_network(network_prefix, strict=False)
            network_validation[network_prefix] = {
                "network": str(network),
                "area_id": area_id,
                "valid": True,
                "devices_in_network": []
            }
        except ValueError as e:
            raise ValueError(f"Invalid network prefix {network_prefix}: {str(e)}")
        
        # Find devices with interfaces in this network
        for device in validated_devices:
            for interface in device["interfaces"]:
                if interface.get("ip_addresses"):
                    for ip in interface["ip_addresses"]:
                        ip_addr = ipaddress.ip_address(ip["address"].split("/")[0])
                        if ip_addr in network:
                            network_validation[network_prefix]["devices_in_network"].append({
                                "device_name": device["device_name"],
                                "interface_name": interface["name"],
                                "ip_address": ip["address"]
                            })
    
    subscription.validated_devices = validated_devices
    subscription.network_validation = network_validation
    subscription.total_devices = len(validated_devices)
    
    return subscription


@configure_ospf.step("Design OSPF Topology")
def design_ospf_topology(subscription: RoutingProvisioning) -> State:
    """Design OSPF area topology and validate configuration"""
    
    # Validate OSPF areas
    area_validation = {}
    backbone_area_exists = False
    
    for area_config in subscription.ospf_areas:
        area_id = area_config.get("area_id")
        area_type = area_config.get("area_type", "normal")
        
        # Validate area ID format
        if area_id == "0" or area_id == "0.0.0.0":
            backbone_area_exists = True
        
        area_validation[area_id] = {
            "area_id": area_id,
            "area_type": area_type,
            "description": area_config.get("area_description", ""),
            "networks": [],
            "devices": set()
        }
    
    if not backbone_area_exists:
        raise ValueError("OSPF Area 0 (backbone area) must be configured")
    
    # Assign networks to areas
    for network_prefix, network_info in subscription.network_validation.items():
        area_id = network_info["area_id"]
        if area_id not in area_validation:
            raise ValueError(f"Network {network_prefix} references undefined area {area_id}")
        
        area_validation[area_id]["networks"].append(network_prefix)
        
        # Add devices to area
        for device_info in network_info["devices_in_network"]:
            area_validation[area_id]["devices"].add(device_info["device_name"])
    
    # Convert device sets to lists for JSON serialization
    for area_id in area_validation:
        area_validation[area_id]["devices"] = list(area_validation[area_id]["devices"])
    
    subscription.ospf_topology = area_validation
    subscription.topology_validated = True
    
    return subscription


@configure_ospf.step("Generate Router IDs")
def generate_router_ids(subscription: RoutingProvisioning) -> State:
    """Generate router IDs for devices that don't have them specified"""
    
    router_id_assignments = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        
        # Use specified router ID or generate one
        if subscription.router_id:
            # If only one device, use the specified router ID
            if len(subscription.validated_devices) == 1:
                router_id_assignments[device_name] = subscription.router_id
            else:
                # For multiple devices, need individual router IDs
                # Generate based on device management IP
                device_ip_parts = device["device_ip"].split(".")
                router_id_assignments[device_name] = device["device_ip"]
        else:
            # Auto-generate router ID from management IP
            router_id_assignments[device_name] = device["device_ip"]
    
    # Validate router IDs are unique
    router_ids = list(router_id_assignments.values())
    if len(router_ids) != len(set(router_ids)):
        raise ValueError("Router IDs must be unique across all OSPF devices")
    
    subscription.router_id_assignments = router_id_assignments
    subscription.router_ids_generated = True
    
    return subscription


@configure_ospf.step("Backup Current Routing Configuration")
def backup_current_routing_config(subscription: RoutingProvisioning) -> State:
    """Backup current routing configuration"""
    
    backup_results = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        device_ip = device["device_ip"]
        device_platform = device["platform"]
        
        # Backup current routing configuration
        backup_result = execute_playbook(
            "ansible/operations/backup_routing_config.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "backup_location": f"backups/ospf_config_{subscription.subscription_id}",
                "include_routing_table": True,
                "include_interfaces": True
            }
        )
        
        backup_results[device_name] = {
            "success": backup_result.get("success", False),
            "backup_path": backup_result.get("backup_path"),
            "backup_id": backup_result.get("backup_id"),
            "error": backup_result.get("error")
        }
    
    subscription.backup_results = backup_results
    subscription.configs_backed_up = all(r["success"] for r in backup_results.values())
    
    return subscription


@configure_ospf.step("Configure OSPF Process")
def configure_ospf_process(subscription: RoutingProvisioning) -> State:
    """Configure OSPF routing process on each device"""
    
    ospf_config_results = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        device_ip = device["device_ip"]
        device_platform = device["platform"]
        router_id = subscription.router_id_assignments[device_name]
        
        # Configure OSPF process
        ospf_result = execute_playbook(
            "ansible/operations/configure_ospf_process.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "ospf_process_id": subscription.ospf_process_id,
                "router_id": router_id,
                "reference_bandwidth": subscription.reference_bandwidth,
                "max_lsa_count": subscription.max_lsa_count,
                "default_route_advertisement": subscription.default_route_advertisement,
                "enable_area_summarization": subscription.enable_area_summarization
            }
        )
        
        ospf_config_results[device_name] = {
            "success": ospf_result.get("success", False),
            "router_id_configured": ospf_result.get("router_id_configured"),
            "process_started": ospf_result.get("process_started", False),
            "error": ospf_result.get("error")
        }
    
    subscription.ospf_config_results = ospf_config_results
    subscription.ospf_processes_configured = all(r["success"] for r in ospf_config_results.values())
    
    return subscription


@configure_ospf.step("Configure OSPF Areas")
def configure_ospf_areas(subscription: RoutingProvisioning) -> State:
    """Configure OSPF areas on devices"""
    
    area_config_results = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        device_ip = device["device_ip"]
        device_platform = device["platform"]
        
        # Find areas this device participates in
        device_areas = []
        for area_id, area_info in subscription.ospf_topology.items():
            if device_name in area_info["devices"]:
                device_areas.append({
                    "area_id": area_id,
                    "area_type": next(a["area_type"] for a in subscription.ospf_areas if a["area_id"] == area_id),
                    "networks": [n for n in area_info["networks"] 
                               if any(d["device_name"] == device_name 
                                     for d in subscription.network_validation[n]["devices_in_network"])]
                })
        
        # Configure areas
        area_result = execute_playbook(
            "ansible/operations/configure_ospf_areas.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "ospf_process_id": subscription.ospf_process_id,
                "areas": device_areas,
                "networks": subscription.networks
            }
        )
        
        area_config_results[device_name] = {
            "success": area_result.get("success", False),
            "areas_configured": area_result.get("areas_configured", []),
            "networks_advertised": area_result.get("networks_advertised", []),
            "error": area_result.get("error")
        }
    
    subscription.area_config_results = area_config_results
    subscription.areas_configured = all(r["success"] for r in area_config_results.values())
    
    return subscription


@configure_ospf.step("Configure OSPF Interfaces")
def configure_ospf_interfaces(subscription: RoutingProvisioning) -> State:
    """Configure OSPF on network interfaces"""
    
    interface_config_results = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        device_ip = device["device_ip"]
        device_platform = device["platform"]
        
        # Configure OSPF interface parameters
        interface_result = execute_playbook(
            "ansible/operations/configure_ospf_interfaces.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "ospf_process_id": subscription.ospf_process_id,
                "hello_interval": subscription.hello_interval,
                "dead_interval": subscription.dead_interval,
                "enable_bfd": subscription.enable_bfd,
                "interfaces": [iface for iface in device["interfaces"] if iface.get("ip_addresses")]
            }
        )
        
        interface_config_results[device_name] = {
            "success": interface_result.get("success", False),
            "interfaces_configured": interface_result.get("interfaces_configured", []),
            "bfd_enabled": interface_result.get("bfd_enabled", False),
            "error": interface_result.get("error")
        }
    
    subscription.interface_config_results = interface_config_results
    subscription.interfaces_configured = all(r["success"] for r in interface_config_results.values())
    
    return subscription


@configure_ospf.step("Configure OSPF Authentication")
def configure_ospf_authentication(subscription: RoutingProvisioning) -> State:
    """Configure OSPF authentication if enabled"""
    
    if not subscription.enable_authentication:
        subscription.authentication_skipped = True
        return subscription
    
    auth_config_results = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        device_ip = device["device_ip"]
        device_platform = device["platform"]
        
        # Configure authentication
        auth_result = execute_playbook(
            "ansible/operations/configure_ospf_authentication.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "ospf_process_id": subscription.ospf_process_id,
                "authentication_type": subscription.authentication_type,
                "authentication_key": subscription.authentication_key,
                "areas": [area["area_id"] for area in subscription.ospf_areas]
            }
        )
        
        auth_config_results[device_name] = {
            "success": auth_result.get("success", False),
            "authentication_configured": auth_result.get("authentication_configured", False),
            "areas_secured": auth_result.get("areas_secured", []),
            "error": auth_result.get("error")
        }
    
    subscription.auth_config_results = auth_config_results
    subscription.authentication_configured = all(r["success"] for r in auth_config_results.values())
    
    return subscription


@configure_ospf.step("Configure Route Filtering")
def configure_route_filtering(subscription: RoutingProvisioning) -> State:
    """Configure route filtering if specified"""
    
    if not subscription.distribute_lists:
        subscription.route_filtering_skipped = True
        return subscription
    
    filter_config_results = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        device_ip = device["device_ip"]
        device_platform = device["platform"]
        
        # Configure distribute lists
        filter_result = execute_playbook(
            "ansible/operations/configure_ospf_filtering.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "ospf_process_id": subscription.ospf_process_id,
                "distribute_lists": subscription.distribute_lists
            }
        )
        
        filter_config_results[device_name] = {
            "success": filter_result.get("success", False),
            "filters_configured": filter_result.get("filters_configured", []),
            "error": filter_result.get("error")
        }
    
    subscription.filter_config_results = filter_config_results
    subscription.route_filtering_configured = all(r["success"] for r in filter_config_results.values())
    
    return subscription


@configure_ospf.step("Verify OSPF Neighbors")
def verify_ospf_neighbors(subscription: RoutingProvisioning) -> State:
    """Verify OSPF neighbor relationships"""
    
    # Wait for OSPF convergence
    import time
    time.sleep(60)
    
    neighbor_verification_results = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        device_ip = device["device_ip"]
        device_platform = device["platform"]
        
        # Verify OSPF neighbors
        neighbor_result = execute_playbook(
            "ansible/operations/verify_ospf_neighbors.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "ospf_process_id": subscription.ospf_process_id,
                "expected_areas": [area["area_id"] for area in subscription.ospf_areas]
            }
        )
        
        neighbor_verification_results[device_name] = {
            "success": neighbor_result.get("success", False),
            "neighbors_found": neighbor_result.get("neighbors_found", 0),
            "neighbor_details": neighbor_result.get("neighbor_details", []),
            "areas_active": neighbor_result.get("areas_active", []),
            "convergence_time": neighbor_result.get("convergence_time", 0),
            "error": neighbor_result.get("error")
        }
    
    subscription.neighbor_verification_results = neighbor_verification_results
    subscription.neighbors_verified = all(r["success"] for r in neighbor_verification_results.values())
    subscription.total_neighbors = sum(r["neighbors_found"] for r in neighbor_verification_results.values())
    
    return subscription


@configure_ospf.step("Verify OSPF Database")
def verify_ospf_database(subscription: RoutingProvisioning) -> State:
    """Verify OSPF database synchronization"""
    
    database_verification_results = {}
    
    for device in subscription.validated_devices:
        device_name = device["device_name"]
        device_ip = device["device_ip"]
        device_platform = device["platform"]
        
        # Verify OSPF database
        db_result = execute_playbook(
            "ansible/operations/verify_ospf_database.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "ospf_process_id": subscription.ospf_process_id
            }
        )
        
        database_verification_results[device_name] = {
            "success": db_result.get("success", False),
            "lsa_count": db_result.get("lsa_count", 0),
            "areas_in_db": db_result.get("areas_in_db", []),
            "router_lsas": db_result.get("router_lsas", 0),
            "network_lsas": db_result.get("network_lsas", 0),
            "external_lsas": db_result.get("external_lsas", 0),
            "error": db_result.get("error")
        }
    
    subscription.database_verification_results = database_verification_results
    subscription.database_synchronized = all(r["success"] for r in database_verification_results.values())
    
    return subscription


@configure_ospf.step("Update NetBox Records")
def update_netbox_records(subscription: RoutingProvisioning) -> State:
    """Update NetBox with OSPF configuration information"""
    
    try:
        # Update device custom fields with OSPF information
        for device in subscription.validated_devices:
            device_name = device["device_name"]
            router_id = subscription.router_id_assignments[device_name]
            
            device_update = {
                "custom_fields": {
                    "ospf_enabled": True,
                    "ospf_process_id": subscription.ospf_process_id,
                    "ospf_router_id": router_id,
                    "ospf_areas": [area for area, info in subscription.ospf_topology.items() 
                                 if device_name in info["devices"]],
                    "ospf_neighbors": subscription.neighbor_verification_results[device_name]["neighbors_found"],
                    "ospf_authentication": subscription.enable_authentication
                }
            }
            
            netbox.update_device(device["device_id"], device_update)
        
        subscription.netbox_updated = True
        
    except Exception as e:
        subscription.netbox_error = str(e)
        subscription.netbox_updated = False
    
    # Create configuration summary
    subscription.ospf_deployment_summary = {
        "total_devices": subscription.total_devices,
        "ospf_process_id": subscription.ospf_process_id,
        "areas_configured": len(subscription.ospf_areas),
        "networks_advertised": len(subscription.networks),
        "total_neighbors": subscription.total_neighbors,
        "authentication_enabled": subscription.enable_authentication,
        "bfd_enabled": subscription.enable_bfd,
        "convergence_successful": subscription.neighbors_verified and subscription.database_synchronized
    }
    
    return subscription


# NetBox Integration Helper Functions

def get_ospf_capable_devices_from_netbox() -> List[tuple]:
    """Get OSPF-capable devices from NetBox"""
    try:
        # Get devices that support OSPF (routers, Layer 3 switches)
        devices = netbox.get_devices(status="active")
        ospf_devices = []
        
        for device in devices:
            device_role = device.get("device_role", {}).get("slug", "")
            device_type = device.get("device_type", {}).get("model", "").lower()
            
            # Check if device is capable of OSPF
            if (any(role in device_role for role in ["router", "l3-switch", "border", "core"]) or
                any(capability in device_type for capability in ["router", "switch", "nexus", "catalyst"])):
                
                site_name = device.get("site", {}).get("name", "Unknown")
                display_name = f"{device['name']} ({site_name})"
                ospf_devices.append((str(device["id"]), display_name))
        
        return ospf_devices if ospf_devices else [("manual", "Manual Device Entry")]
    except:
        return [("manual", "Manual Device Entry")]


def get_sites_from_netbox() -> List[tuple]:
    """Get sites from NetBox for area discovery"""
    try:
        sites = netbox.get_sites(status="active")
        site_options = [("", "All Sites")]
        
        for site in sites:
            site_options.append((site["slug"], f"{site['name']} ({site['slug']})"))
        
        return site_options
    except:
        return [("", "All Sites")]


def get_default_ospf_areas_from_netbox() -> List[Dict[str, Any]]:
    """Get default OSPF areas from NetBox configuration"""
    try:
        # Try to get OSPF area design from NetBox
        ospf_config = netbox.get_custom_config("ospf_areas")
        if ospf_config:
            return ospf_config
    except:
        pass
    
    # Return standard backbone area
    return [{
        "area_id": "0.0.0.0",
        "area_type": "backbone",
        "area_description": "Backbone Area"
    }]


def get_ospf_auth_policy_from_netbox() -> bool:
    """Get OSPF authentication policy from NetBox"""
    try:
        security_policy = netbox.get_custom_config("security_policy")
        if security_policy:
            return security_policy.get("ospf_authentication_required", False)
    except:
        pass
    return False


def get_supported_auth_types_from_netbox() -> List[tuple]:
    """Get supported authentication types from NetBox security policy"""
    try:
        security_policy = netbox.get_custom_config("security_policy")
        if security_policy and "ospf_auth_types" in security_policy:
            auth_types = []
            for auth_type in security_policy["ospf_auth_types"]:
                if auth_type == "simple":
                    auth_types.append(("simple", "Simple Password"))
                elif auth_type == "md5":
                    auth_types.append(("md5", "MD5 Authentication"))
                elif auth_type == "sha":
                    auth_types.append(("sha", "SHA Authentication"))
            return auth_types
    except:
        pass
    
    return [
        ("simple", "Simple Password"),
        ("md5", "MD5 Authentication"),
        ("sha", "SHA Authentication")
    ]


def auto_discover_ospf_networks_from_netbox(site_filter: str, target_devices: List[str]) -> List[Dict[str, Any]]:
    """Auto-discover OSPF networks from NetBox prefixes"""
    networks = []
    
    try:
        # Get prefixes based on site filter
        filter_params = {"status": "active"}
        if site_filter:
            filter_params["site"] = site_filter
        
        prefixes = netbox.get_prefixes(**filter_params)
        
        for prefix in prefixes:
            # Skip pool prefixes
            if prefix.get("is_pool", False):
                continue
            
            # Check if prefix is associated with target devices
            if prefix.get("role"):
                role_slug = prefix["role"]["slug"]
                if any(role in role_slug for role in ["infrastructure", "loopback", "p2p", "transit"]):
                    networks.append({
                        "network": prefix["prefix"],
                        "area": "0.0.0.0",  # Default to backbone
                        "description": f"Auto-discovered from NetBox - {prefix.get('description', '')}"
                    })
    except:
        pass
    
    return networks


def get_ospf_areas_from_site_topology(site_filter: str) -> List[Dict[str, Any]]:
    """Generate OSPF areas based on site topology in NetBox"""
    areas = []
    
    try:
        if not site_filter:
            # Multi-site deployment
            sites = netbox.get_sites(status="active")
            
            # Backbone area
            areas.append({
                "area_id": "0.0.0.0",
                "area_type": "backbone",
                "area_description": "Multi-site backbone area"
            })
            
            # Site-specific areas
            for i, site in enumerate(sites[:10], start=1):  # Limit to 10 sites
                areas.append({
                    "area_id": f"0.0.0.{i}",
                    "area_type": "standard",
                    "area_description": f"Area for site {site['name']}"
                })
        else:
            # Single site deployment
            site_info = netbox.get_site(site_filter)
            areas.append({
                "area_id": "0.0.0.0",
                "area_type": "backbone",
                "area_description": f"Backbone area for {site_info.get('name', site_filter)}"
            })
    except:
        pass
    
    return areas if areas else get_default_ospf_areas_from_netbox()


def get_router_id_from_netbox(device_id: str) -> Optional[str]:
    """Get router ID from NetBox device management IP"""
    try:
        device = netbox.get_device(device_id)
        if device and device.get("primary_ip4"):
            # Use the management IP as router ID
            return device["primary_ip4"]["address"].split("/")[0]
    except:
        pass
    return None
