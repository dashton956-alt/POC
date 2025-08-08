"""
Port Channel/LAG Configuration Workflow
Create and manage link aggregation groups for high availability
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

from products.product_types.port import PortInactive, PortProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from services.api_manager import api_manager, get_device_connection
from services.device_connector import device_connection_manager, connect_to_device, deploy_device_configuration, execute_device_command
from workflows.shared import device_selector, port_selector


class PortChannelForm(FormPage):
    """Port Channel/LAG Configuration Form"""
    
    # Target Device - NetBox driven
    target_device: str = Field(
        description="Target Device for Port Channel",
        choices=get_lag_capable_devices_from_netbox()
    )
    
    # Port Channel Identity
    portchannel_name: str = Field(
        description="Port Channel Name",
        regex=r'^[a-zA-Z0-9\-_]+$',
        min_length=1,
        max_length=32
    )
    
    portchannel_id: int = Field(
        description="Port Channel ID (auto-suggest next available)",
        ge=1,
        le=4096,
        default=get_next_available_portchannel_id()
    )
    
    portchannel_description: str = Field(
        description="Port Channel Description",
        default=""
    )
    
    # Member Port Selection - NetBox interface integration
    member_ports: List[str] = Field(
        description="Member Ports (filtered by device and availability)",
        min_items=2,
        max_items=16,
        choices=get_available_interfaces_from_netbox()
    )
    
    # LAG Configuration - Platform-aware
    lag_protocol: Choice = Field(
        description="LAG Protocol (filtered by device capability)",
        choices=get_supported_lag_protocols_from_netbox(),
        default="lacp"
    )
    
    lacp_mode: Choice = Field(
        description="LACP Mode",
        choices=[
            ("active", "Active"),
            ("passive", "Passive")
        ],
        default="active"
    )
    
    # Load Balancing - Platform-specific options
    load_balancing: Choice = Field(
        description="Load Balancing Algorithm",
        choices=get_supported_load_balancing_from_netbox(),
        default="src_dst_ip"
    )
    
    # VLAN Configuration - NetBox VLAN integration
    native_vlan: Optional[int] = Field(
        description="Native VLAN ID",
        ge=1,
        le=4094,
        choices=get_available_vlans_from_netbox(),
        default=None
    )
    
    allowed_vlans: str = Field(
        description="Allowed VLANs (populated from NetBox VLAN groups)",
        default=get_default_vlan_range_from_netbox()
    )
    
    # Port Channel Interface Configuration
    interface_mode: Choice = Field(
        description="Interface Mode",
        choices=[
            ("access", "Access"),
            ("trunk", "Trunk"),
            ("hybrid", "Hybrid")
        ],
        default="trunk"
    )
    
    # Speed and Duplex
    speed: Choice = Field(
        description="Interface Speed",
        choices=[
            ("auto", "Auto-negotiate"),
            ("10", "10 Mbps"),
            ("100", "100 Mbps"),
            ("1000", "1 Gbps"),
            ("10000", "10 Gbps"),
            ("25000", "25 Gbps"),
            ("40000", "40 Gbps"),
            ("100000", "100 Gbps")
        ],
        default="auto"
    )
    
    # Redundancy Options
    min_links: int = Field(
        description="Minimum Active Links",
        ge=1,
        le=16,
        default=1
    )
    
    max_links: int = Field(
        description="Maximum Active Links",
        ge=1,
        le=16,
        default=16
    )
    
    # Advanced Options
    enable_fast_switchover: bool = Field(
        description="Enable Fast Switchover",
        default=True
    )
    
    lacp_timeout: Choice = Field(
        description="LACP Timeout",
        choices=[
            ("short", "Short (1 second)"),
            ("long", "Long (30 seconds)")
        ],
        default="long"
    )


@workflow("Configure Port Channel/LAG", target=Target.CREATE)
def configure_port_channel(subscription: PortInactive) -> State:
    """Configure port channel/LAG workflow"""
    return (
        begin
        >> store_process_subscription(subscription)
        >> validate_member_ports
        >> check_port_availability
        >> validate_port_channel_config
        >> backup_current_config
        >> configure_member_ports
        >> create_port_channel_interface
        >> configure_load_balancing
        >> verify_port_channel_status
        >> update_netbox_records
        >> done
    )


@configure_port_channel.step("Validate Member Ports")
def validate_member_ports(subscription: PortProvisioning) -> State:
    """Validate member ports and their compatibility"""
    
    validated_ports = []
    device_info = {}
    
    for port_id in subscription.member_ports:
        # Get port information from NetBox
        port_info = netbox.get_interface(port_id)
        if not port_info:
            raise ValueError(f"Port {port_id} not found in NetBox")
        
        # Get device information
        device = port_info.get("device", {})
        device_id = device.get("id")
        
        if not device_info:
            device_info = {
                "device_id": device_id,
                "device_name": device.get("name"),
                "device_ip": device.get("primary_ip4", {}).get("address", "").split("/")[0],
                "platform": device.get("platform", {}).get("slug"),
                "vendor": device.get("device_type", {}).get("manufacturer", {}).get("slug")
            }
        elif device_info["device_id"] != device_id:
            raise ValueError("All member ports must be on the same device")
        
        # Validate port compatibility
        port_type = port_info.get("type", {}).get("value")
        port_speed = port_info.get("speed")
        
        validated_ports.append({
            "port_id": port_id,
            "port_name": port_info.get("name"),
            "port_type": port_type,
            "port_speed": port_speed,
            "current_status": port_info.get("enabled", False),
            "description": port_info.get("description", "")
        })
    
    # Validate all ports have compatible speeds
    speeds = [p["port_speed"] for p in validated_ports if p["port_speed"]]
    if len(set(speeds)) > 1:
        raise ValueError("All member ports must have the same speed")
    
    subscription.validated_ports = validated_ports
    subscription.device_info = device_info
    subscription.port_count = len(validated_ports)
    
    return subscription


@configure_port_channel.step("Check Port Availability")
def check_port_availability(subscription: PortProvisioning) -> State:
    """Check if ports are available for LAG configuration"""
    
    device_ip = subscription.device_info["device_ip"]
    device_platform = subscription.device_info["platform"]
    
    # Check port status and configuration
    port_status_result = execute_playbook(
        "ansible/operations/check_port_status.yaml",
        extra_vars={
            "device_ip": device_ip,
            "device_platform": device_platform,
            "ports": [p["port_name"] for p in subscription.validated_ports]
        }
    )
    
    if not port_status_result.get("success"):
        raise RuntimeError(f"Failed to check port status: {port_status_result.get('error')}")
    
    port_statuses = port_status_result.get("port_statuses", {})
    unavailable_ports = []
    
    for port in subscription.validated_ports:
        port_name = port["port_name"]
        status = port_statuses.get(port_name, {})
        
        # Check if port is already in a LAG
        if status.get("in_portchannel"):
            unavailable_ports.append(f"{port_name} (already in LAG {status.get('portchannel_id')})")
        
        # Check if port has active connections
        if status.get("operational_status") == "up" and status.get("has_active_sessions"):
            unavailable_ports.append(f"{port_name} (has active connections)")
        
        port["current_operational_status"] = status.get("operational_status", "unknown")
        port["current_admin_status"] = status.get("admin_status", "unknown")
        port["in_portchannel"] = status.get("in_portchannel", False)
    
    if unavailable_ports:
        raise ValueError(f"The following ports are unavailable: {', '.join(unavailable_ports)}")
    
    subscription.ports_available = True
    subscription.port_statuses = port_statuses
    
    return subscription


@configure_port_channel.step("Validate Port Channel Configuration")
def validate_port_channel_config(subscription: PortProvisioning) -> State:
    """Validate port channel configuration parameters"""
    
    device_ip = subscription.device_info["device_ip"]
    device_platform = subscription.device_info["platform"]
    
    # Check if port channel ID is available
    pc_check_result = execute_playbook(
        "ansible/operations/check_portchannel_availability.yaml",
        extra_vars={
            "device_ip": device_ip,
            "device_platform": device_platform,
            "portchannel_id": subscription.portchannel_id
        }
    )
    
    if not pc_check_result.get("available"):
        raise ValueError(f"Port Channel ID {subscription.portchannel_id} is already in use")
    
    # Validate VLAN configuration
    if subscription.native_vlan or subscription.allowed_vlans != "all":
        vlan_result = execute_playbook(
            "ansible/operations/validate_vlan_config.yaml",
            extra_vars={
                "device_ip": device_ip,
                "device_platform": device_platform,
                "native_vlan": subscription.native_vlan,
                "allowed_vlans": subscription.allowed_vlans
            }
        )
        
        if not vlan_result.get("success"):
            raise ValueError(f"VLAN validation failed: {vlan_result.get('error')}")
    
    # Validate min/max links
    if subscription.min_links > subscription.port_count:
        raise ValueError(f"Minimum links ({subscription.min_links}) cannot exceed number of member ports ({subscription.port_count})")
    
    if subscription.max_links > subscription.port_count:
        subscription.max_links = subscription.port_count
    
    subscription.config_validated = True
    
    return subscription


@configure_port_channel.step("Backup Current Configuration")
def backup_current_config(subscription: PortProvisioning) -> State:
    """Backup current port and device configuration"""
    
    device_ip = subscription.device_info["device_ip"]
    device_platform = subscription.device_info["platform"]
    
    # Backup current configuration
    backup_result = execute_playbook(
        "ansible/operations/backup_port_config.yaml",
        extra_vars={
            "device_ip": device_ip,
            "device_platform": device_platform,
            "ports": [p["port_name"] for p in subscription.validated_ports],
            "backup_location": f"backups/portchannel_config_{subscription.subscription_id}",
            "include_global_config": True
        }
    )
    
    if not backup_result.get("success"):
        raise RuntimeError(f"Failed to backup configuration: {backup_result.get('error')}")
    
    subscription.backup_id = backup_result.get("backup_id")
    subscription.backup_path = backup_result.get("backup_path")
    subscription.config_backed_up = True
    
    return subscription


@configure_port_channel.step("Configure Member Ports")
def configure_member_ports(subscription: PortProvisioning) -> State:
    """Configure individual member ports for LAG"""
    
    device_ip = subscription.device_info["device_ip"]
    device_platform = subscription.device_info["platform"]
    
    # Configure each member port
    member_config_result = execute_playbook(
        "ansible/operations/configure_lag_member_ports.yaml",
        extra_vars={
            "device_ip": device_ip,
            "device_platform": device_platform,
            "member_ports": subscription.validated_ports,
            "portchannel_id": subscription.portchannel_id,
            "lag_protocol": subscription.lag_protocol,
            "lacp_mode": subscription.lacp_mode,
            "lacp_timeout": subscription.lacp_timeout,
            "speed": subscription.speed
        }
    )
    
    if not member_config_result.get("success"):
        raise RuntimeError(f"Failed to configure member ports: {member_config_result.get('error')}")
    
    subscription.member_ports_configured = True
    subscription.member_config_results = member_config_result.get("port_results", {})
    
    return subscription


@configure_port_channel.step("Create Port Channel Interface")
def create_port_channel_interface(subscription: PortProvisioning) -> State:
    """Create and configure the port channel interface"""
    
    device_ip = subscription.device_info["device_ip"]
    device_platform = subscription.device_info["platform"]
    
    # Create port channel interface
    pc_config_result = execute_playbook(
        "ansible/operations/create_portchannel_interface.yaml",
        extra_vars={
            "device_ip": device_ip,
            "device_platform": device_platform,
            "portchannel_name": subscription.portchannel_name,
            "portchannel_id": subscription.portchannel_id,
            "portchannel_description": subscription.portchannel_description,
            "interface_mode": subscription.interface_mode,
            "native_vlan": subscription.native_vlan,
            "allowed_vlans": subscription.allowed_vlans,
            "min_links": subscription.min_links,
            "max_links": subscription.max_links,
            "enable_fast_switchover": subscription.enable_fast_switchover
        }
    )
    
    if not pc_config_result.get("success"):
        raise RuntimeError(f"Failed to create port channel interface: {pc_config_result.get('error')}")
    
    subscription.portchannel_interface_created = True
    subscription.portchannel_config = pc_config_result.get("portchannel_config", {})
    
    return subscription


@configure_port_channel.step("Configure Load Balancing")
def configure_load_balancing(subscription: PortProvisioning) -> State:
    """Configure load balancing algorithm"""
    
    device_ip = subscription.device_info["device_ip"]
    device_platform = subscription.device_info["platform"]
    
    # Configure load balancing
    lb_config_result = execute_playbook(
        "ansible/operations/configure_portchannel_load_balancing.yaml",
        extra_vars={
            "device_ip": device_ip,
            "device_platform": device_platform,
            "portchannel_id": subscription.portchannel_id,
            "load_balancing": subscription.load_balancing
        }
    )
    
    if not lb_config_result.get("success"):
        # Log warning but don't fail - some platforms may not support this
        subscription.load_balancing_warning = lb_config_result.get("error")
        subscription.load_balancing_configured = False
    else:
        subscription.load_balancing_configured = True
    
    return subscription


@configure_port_channel.step("Verify Port Channel Status")
def verify_port_channel_status(subscription: PortProvisioning) -> State:
    """Verify port channel is operational"""
    
    device_ip = subscription.device_info["device_ip"]
    device_platform = subscription.device_info["platform"]
    
    # Wait for convergence (LAG protocols need time to negotiate)
    import time
    time.sleep(30)
    
    # Verify port channel status
    verify_result = execute_playbook(
        "ansible/operations/verify_portchannel_status.yaml",
        extra_vars={
            "device_ip": device_ip,
            "device_platform": device_platform,
            "portchannel_id": subscription.portchannel_id,
            "expected_member_count": subscription.port_count,
            "min_links": subscription.min_links
        }
    )
    
    if not verify_result.get("success"):
        raise RuntimeError(f"Port channel verification failed: {verify_result.get('error')}")
    
    status_info = verify_result.get("portchannel_status", {})
    
    subscription.portchannel_operational = status_info.get("operational_status") == "up"
    subscription.active_member_count = status_info.get("active_members", 0)
    subscription.inactive_member_count = status_info.get("inactive_members", 0)
    subscription.protocol_status = status_info.get("protocol_status", {})
    
    # Check if minimum links requirement is met
    if subscription.active_member_count < subscription.min_links:
        raise RuntimeError(f"Port channel has only {subscription.active_member_count} active members, minimum required is {subscription.min_links}")
    
    subscription.verification_completed = True
    
    return subscription


@configure_port_channel.step("Update NetBox Records")
def update_netbox_records(subscription: PortProvisioning) -> State:
    """Update NetBox with port channel configuration"""
    
    try:
        # Create port channel interface in NetBox
        portchannel_data = {
            "device": subscription.device_info["device_id"],
            "name": f"Port-channel{subscription.portchannel_id}",
            "type": "lag",
            "description": subscription.portchannel_description,
            "enabled": True,
            "mode": subscription.interface_mode,
            "custom_fields": {
                "portchannel_id": subscription.portchannel_id,
                "lag_protocol": subscription.lag_protocol,
                "lacp_mode": subscription.lacp_mode if subscription.lag_protocol == "lacp" else None,
                "load_balancing": subscription.load_balancing,
                "min_links": subscription.min_links,
                "max_links": subscription.max_links,
                "member_count": subscription.port_count,
                "active_members": subscription.active_member_count
            }
        }
        
        portchannel_interface = netbox.create_interface(portchannel_data)
        subscription.netbox_portchannel_id = portchannel_interface.get("id")
        
        # Update member port interfaces
        for port in subscription.validated_ports:
            member_update = {
                "lag": subscription.netbox_portchannel_id,
                "description": f"Member of Port-channel{subscription.portchannel_id}",
                "custom_fields": {
                    "lag_member": True,
                    "portchannel_id": subscription.portchannel_id
                }
            }
            
            netbox.update_interface(port["port_id"], member_update)
        
        subscription.netbox_updated = True
        
    except Exception as e:
        # Log error but don't fail workflow
        subscription.netbox_error = str(e)
        subscription.netbox_updated = False
    
    return subscription


# NetBox Integration Helper Functions

def get_lag_capable_devices_from_netbox() -> List[tuple]:
    """Get LAG-capable devices from NetBox"""
    try:
        devices = netbox.get_devices(status="active")
        lag_devices = []
        
        for device in devices:
            device_type = device.get("device_type", {}).get("model", "").lower()
            device_role = device.get("device_role", {}).get("slug", "")
            
            # Check if device supports LAG/port-channel
            if (any(role in device_role for role in ["switch", "router", "access", "distribution", "core"]) or
                any(capability in device_type for capability in ["switch", "router", "nexus", "catalyst", "arista"])):
                
                site_name = device.get("site", {}).get("name", "Unknown")
                display_name = f"{device['name']} ({site_name})"
                lag_devices.append((str(device["id"]), display_name))
        
        return lag_devices if lag_devices else [("manual", "Manual Device Entry")]
    except:
        return [("manual", "Manual Device Entry")]


def get_next_available_portchannel_id() -> int:
    """Get next available port channel ID from NetBox"""
    try:
        # Query existing port channels to find next available ID
        interfaces = netbox.get_interfaces(type="lag")
        used_ids = set()
        
        for interface in interfaces:
            # Extract ID from interface name (e.g., Port-channel1 -> 1)
            name = interface.get("name", "")
            if "port-channel" in name.lower():
                try:
                    id_part = name.lower().replace("port-channel", "").replace("po", "")
                    used_ids.add(int(id_part))
                except:
                    pass
        
        # Find first available ID
        for i in range(1, 4097):
            if i not in used_ids:
                return i
        
        return 1  # Default fallback
    except:
        return 1


def get_available_interfaces_from_netbox() -> List[tuple]:
    """Get available interfaces for LAG membership"""
    try:
        # This would be dynamically filtered based on selected device
        # For now, return placeholder that would be populated by JavaScript
        return [
            ("auto_discover", "Auto-discover from selected device")
        ]
    except:
        return [("manual", "Manual Interface Entry")]


def get_supported_lag_protocols_from_netbox() -> List[tuple]:
    """Get supported LAG protocols based on device platform"""
    try:
        # This could be enhanced to check device platform capabilities
        platforms = netbox.get_platforms()
        protocols = set()
        
        for platform in platforms:
            manufacturer = platform.get("manufacturer", {}).get("slug", "")
            if manufacturer == "cisco":
                protocols.update(["lacp", "pagp", "static"])
            elif manufacturer in ["juniper", "arista", "cumulus"]:
                protocols.update(["lacp", "static"])
            else:
                protocols.add("lacp")  # Universal support
        
        protocol_options = []
        if "lacp" in protocols:
            protocol_options.append(("lacp", "LACP (802.3ad)"))
        if "static" in protocols:
            protocol_options.append(("static", "Static LAG"))
        if "pagp" in protocols:
            protocol_options.append(("pagp", "PAgP (Cisco Proprietary)"))
        
        return protocol_options if protocol_options else [("lacp", "LACP (802.3ad)")]
    except:
        return [
            ("lacp", "LACP (802.3ad)"),
            ("static", "Static LAG"),
            ("pagp", "PAgP (Cisco Proprietary)")
        ]


def get_supported_load_balancing_from_netbox() -> List[tuple]:
    """Get supported load balancing algorithms"""
    try:
        # Could be enhanced to check platform-specific algorithms
        return [
            ("src_dst_ip", "Source-Destination IP"),
            ("src_dst_mac", "Source-Destination MAC"),
            ("src_dst_port", "Source-Destination Port"),
            ("src_ip", "Source IP"),
            ("dst_ip", "Destination IP"),
            ("round_robin", "Round Robin")
        ]
    except:
        return [("src_dst_ip", "Source-Destination IP")]


def get_available_vlans_from_netbox() -> List[tuple]:
    """Get available VLANs from NetBox"""
    try:
        vlans = netbox.get_vlans(status="active")
        vlan_options = [("", "No Native VLAN")]
        
        for vlan in vlans:
            vlan_options.append((str(vlan["vid"]), f"VLAN {vlan['vid']} - {vlan['name']}"))
        
        return vlan_options
    except:
        return [("", "No Native VLAN")]


def get_default_vlan_range_from_netbox() -> str:
    """Get default VLAN range from NetBox VLAN groups"""
    try:
        vlan_groups = netbox.get_vlan_groups()
        if vlan_groups:
            # Use first VLAN group's range
            first_group = vlan_groups[0]
            vlans = netbox.get_vlans(group=first_group["id"])
            if vlans:
                vlan_ids = sorted([v["vid"] for v in vlans])
                if len(vlan_ids) > 1:
                    return f"{vlan_ids[0]}-{vlan_ids[-1]}"
                else:
                    return str(vlan_ids[0])
    except:
        pass
    
    return "all"


def get_interface_speed_from_netbox(interface_id: str) -> Optional[str]:
    """Get interface speed from NetBox"""
    try:
        interface = netbox.get_interface(interface_id)
        if interface and interface.get("type"):
            # Map interface type to speed
            interface_type = interface["type"]["value"]
            speed_mapping = {
                "1000base-t": "1G",
                "10gbase-x": "10G",
                "25gbase-x": "25G",
                "40gbase-x": "40G",
                "100gbase-x": "100G"
            }
            return speed_mapping.get(interface_type.lower(), "Unknown")
    except:
        pass
    
    return None
