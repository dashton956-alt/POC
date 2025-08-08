"""
Delete VLAN Workflow
Remove VLAN configuration and cleanup resources across network infrastructure
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

from products.product_types.vlan import VLANInactive, VLANProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from services.api_manager import api_manager, get_device_connection
from services.device_connector import device_connection_manager, connect_to_device, deploy_device_configuration, execute_device_command
from workflows.shared import device_selectorflow
Remove unused VLAN and cleanup associated resources
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

from products.product_types.vlan import VLANInactive, VLANProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from workflows.shared import vlan_selector


class DeleteVLANForm(FormPage):
    """Delete VLAN Form"""
    
    # VLAN Selection
    vlan_id: int = Field(
        description="VLAN ID to Delete",
        ge=1,
        le=4094
    )
    
    vlan_name: str = Field(
        description="VLAN Name (for confirmation)",
        min_length=1
    )
    
    # Safety Options
    force_delete: bool = Field(
        description="Force Delete (ignore dependencies)",
        default=False
    )
    
    preserve_config: bool = Field(
        description="Preserve Configuration as Backup",
        default=True
    )
    
    # Migration Options
    migrate_interfaces: bool = Field(
        description="Migrate Interfaces to Different VLAN",
        default=False
    )
    
    migration_target_vlan: Optional[int] = Field(
        description="Target VLAN for Interface Migration",
        ge=1,
        le=4094,
        default=None
    )
    
    # Cleanup Options
    cleanup_ip_addresses: bool = Field(
        description="Cleanup Associated IP Addresses",
        default=True
    )
    
    cleanup_dhcp_pools: bool = Field(
        description="Cleanup DHCP Pools",
        default=True
    )
    
    cleanup_routing_entries: bool = Field(
        description="Cleanup Routing Table Entries",
        default=True
    )
    
    # Confirmation
    confirmation_string: str = Field(
        description="Type 'DELETE' to confirm",
        regex=r'^DELETE$'
    )
    
    @validator('migration_target_vlan')
    def validate_migration_target(cls, v, values):
        if values.get('migrate_interfaces') and not v:
            raise ValueError("Migration target VLAN is required when migrate_interfaces is enabled")
        return v


@workflow("Delete VLAN", target=Target.TERMINATE)
def delete_vlan(subscription: VLANInactive) -> State:
    """Delete VLAN workflow"""
    return (
        begin
        >> store_process_subscription(subscription)
        >> validate_vlan_exists
        >> analyze_vlan_dependencies
        >> check_safety_constraints
        >> backup_vlan_configuration
        >> migrate_interfaces_if_requested
        >> remove_vlan_from_devices
        >> cleanup_ip_resources
        >> cleanup_dhcp_resources
        >> cleanup_routing_resources
        >> update_netbox_records
        >> done
    )


@delete_vlan.step("Validate VLAN Exists")
def validate_vlan_exists(subscription: VLANProvisioning) -> State:
    """Validate VLAN exists and get detailed information"""
    
    # Get VLAN information from NetBox
    vlan_info = netbox.get_vlan(subscription.vlan_id)
    if not vlan_info:
        raise ValueError(f"VLAN {subscription.vlan_id} not found in NetBox")
    
    # Verify VLAN name matches for safety
    if vlan_info.get("name") != subscription.vlan_name:
        raise ValueError(f"VLAN name mismatch. Expected: {subscription.vlan_name}, Found: {vlan_info.get('name')}")
    
    # Get VLAN details
    subscription.vlan_info = {
        "vlan_id": vlan_info.get("vid"),
        "name": vlan_info.get("name"),
        "description": vlan_info.get("description", ""),
        "site": vlan_info.get("site", {}).get("name", ""),
        "tenant": vlan_info.get("tenant", {}).get("name", "") if vlan_info.get("tenant") else "",
        "role": vlan_info.get("role", {}).get("name", "") if vlan_info.get("role") else "",
        "status": vlan_info.get("status", {}).get("value", ""),
        "created": vlan_info.get("created"),
        "last_updated": vlan_info.get("last_updated")
    }
    
    # Get associated subnet information
    subnets = netbox.get_vlan_subnets(subscription.vlan_id)
    subscription.associated_subnets = subnets
    
    subscription.vlan_validated = True
    
    return subscription


@delete_vlan.step("Analyze VLAN Dependencies")
def analyze_vlan_dependencies(subscription: VLANProvisioning) -> State:
    """Analyze VLAN dependencies and usage"""
    
    dependencies = {}
    
    # Find interfaces using this VLAN
    interfaces = netbox.get_vlan_interfaces(subscription.vlan_id)
    dependencies["interfaces"] = [
        {
            "interface_id": iface.get("id"),
            "interface_name": iface.get("name"),
            "device_name": iface.get("device", {}).get("name", ""),
            "device_id": iface.get("device", {}).get("id"),
            "mode": iface.get("mode", {}).get("value", ""),
            "untagged_vlan": iface.get("untagged_vlan", {}).get("vid") == subscription.vlan_id,
            "tagged_vlans": subscription.vlan_id in [v.get("vid") for v in iface.get("tagged_vlans", [])]
        }
        for iface in interfaces
    ]
    
    # Find IP addresses in VLAN subnets
    ip_addresses = []
    for subnet in subscription.associated_subnets:
        subnet_ips = netbox.get_subnet_ip_addresses(subnet["id"])
        ip_addresses.extend([
            {
                "ip_id": ip.get("id"),
                "address": ip.get("address"),
                "status": ip.get("status", {}).get("value", ""),
                "assigned_object": ip.get("assigned_object"),
                "subnet_id": subnet["id"],
                "subnet_prefix": subnet["prefix"]
            }
            for ip in subnet_ips
        ])
    dependencies["ip_addresses"] = ip_addresses
    
    # Find DHCP pools/scopes
    dhcp_pools = netbox.get_vlan_dhcp_pools(subscription.vlan_id)
    dependencies["dhcp_pools"] = dhcp_pools
    
    # Find routing table entries
    routes = netbox.get_routes_for_vlan(subscription.vlan_id)
    dependencies["routes"] = routes
    
    # Find services using this VLAN
    services = netbox.get_vlan_services(subscription.vlan_id)
    dependencies["services"] = services
    
    # Find VPN connections
    vpn_connections = netbox.get_vlan_vpn_connections(subscription.vlan_id)
    dependencies["vpn_connections"] = vpn_connections
    
    subscription.vlan_dependencies = dependencies
    subscription.total_dependencies = (
        len(dependencies["interfaces"]) +
        len(dependencies["ip_addresses"]) +
        len(dependencies["dhcp_pools"]) +
        len(dependencies["routes"]) +
        len(dependencies["services"]) +
        len(dependencies["vpn_connections"])
    )
    
    return subscription


@delete_vlan.step("Check Safety Constraints")
def check_safety_constraints(subscription: VLANProvisioning) -> State:
    """Check safety constraints before deletion"""
    
    safety_violations = []
    
    # Check for active services
    active_services = [s for s in subscription.vlan_dependencies["services"] if s.get("status") == "active"]
    if active_services and not subscription.force_delete:
        safety_violations.append(f"{len(active_services)} active services are using this VLAN")
    
    # Check for assigned IP addresses
    assigned_ips = [ip for ip in subscription.vlan_dependencies["ip_addresses"] if ip.get("status") == "active"]
    if assigned_ips and not subscription.force_delete:
        safety_violations.append(f"{len(assigned_ips)} IP addresses are currently assigned")
    
    # Check for trunk interfaces (more critical)
    trunk_interfaces = [
        iface for iface in subscription.vlan_dependencies["interfaces"] 
        if iface.get("mode") == "tagged" and iface.get("tagged_vlans")
    ]
    if trunk_interfaces and not subscription.force_delete:
        safety_violations.append(f"{len(trunk_interfaces)} trunk interfaces carry this VLAN")
    
    # Check for access interfaces
    access_interfaces = [
        iface for iface in subscription.vlan_dependencies["interfaces"]
        if iface.get("untagged_vlan")
    ]
    if access_interfaces and not subscription.migrate_interfaces and not subscription.force_delete:
        safety_violations.append(f"{len(access_interfaces)} access interfaces use this VLAN as untagged")
    
    # Check for VPN connections
    active_vpns = [vpn for vpn in subscription.vlan_dependencies["vpn_connections"] if vpn.get("status") == "active"]
    if active_vpns and not subscription.force_delete:
        safety_violations.append(f"{len(active_vpns)} VPN connections are using this VLAN")
    
    if safety_violations:
        raise ValueError(f"Safety constraints violated: {'; '.join(safety_violations)}. Use force_delete=True to override.")
    
    subscription.safety_check_passed = True
    
    return subscription


@delete_vlan.step("Backup VLAN Configuration")
def backup_vlan_configuration(subscription: VLANProvisioning) -> State:
    """Backup VLAN configuration before deletion"""
    
    if not subscription.preserve_config:
        subscription.backup_skipped = True
        return subscription
    
    # Create comprehensive backup
    backup_data = {
        "vlan_info": subscription.vlan_info,
        "dependencies": subscription.vlan_dependencies,
        "deletion_timestamp": subscription.workflow_start_time,
        "deletion_reason": "User requested deletion",
        "force_delete": subscription.force_delete,
        "migration_performed": subscription.migrate_interfaces
    }
    
    # Get device configurations for this VLAN
    device_configs = {}
    unique_devices = set()
    
    for interface in subscription.vlan_dependencies["interfaces"]:
        unique_devices.add(interface["device_id"])
    
    for device_id in unique_devices:
        device_info = netbox.get_device(device_id)
        device_ip = device_info.get("primary_ip4", {}).get("address", "").split("/")[0]
        
        if device_ip:
            # Backup device VLAN configuration
            backup_result = execute_playbook(
                "ansible/operations/backup_vlan_config.yaml",
                extra_vars={
                    "device_ip": device_ip,
                    "device_platform": device_info.get("platform", {}).get("slug", "unknown"),
                    "vlan_id": subscription.vlan_id,
                    "backup_location": f"backups/vlan_deletion_{subscription.vlan_id}_{subscription.subscription_id}"
                }
            )
            
            if backup_result.get("success"):
                device_configs[device_id] = backup_result.get("backup_path")
    
    subscription.backup_data = backup_data
    subscription.device_config_backups = device_configs
    subscription.config_backed_up = True
    
    return subscription


@delete_vlan.step("Migrate Interfaces If Requested")
def migrate_interfaces_if_requested(subscription: VLANProvisioning) -> State:
    """Migrate interfaces to different VLAN if requested"""
    
    if not subscription.migrate_interfaces:
        subscription.migration_skipped = True
        return subscription
    
    # Validate target VLAN exists
    target_vlan_info = netbox.get_vlan(subscription.migration_target_vlan)
    if not target_vlan_info:
        raise ValueError(f"Migration target VLAN {subscription.migration_target_vlan} not found")
    
    migration_results = {}
    
    # Migrate access interfaces (untagged VLAN)
    access_interfaces = [
        iface for iface in subscription.vlan_dependencies["interfaces"]
        if iface.get("untagged_vlan")
    ]
    
    for interface in access_interfaces:
        device_info = netbox.get_device(interface["device_id"])
        device_ip = device_info.get("primary_ip4", {}).get("address", "").split("/")[0]
        
        if device_ip:
            # Migrate interface VLAN
            migrate_result = execute_playbook(
                "ansible/operations/migrate_interface_vlan.yaml",
                extra_vars={
                    "device_ip": device_ip,
                    "device_platform": device_info.get("platform", {}).get("slug"),
                    "interface_name": interface["interface_name"],
                    "source_vlan": subscription.vlan_id,
                    "target_vlan": subscription.migration_target_vlan
                }
            )
            
            migration_results[interface["interface_id"]] = {
                "success": migrate_result.get("success", False),
                "error": migrate_result.get("error"),
                "interface_name": interface["interface_name"],
                "device_name": interface["device_name"]
            }
            
            # Update NetBox interface record
            if migrate_result.get("success"):
                try:
                    netbox.update_interface(interface["interface_id"], {
                        "untagged_vlan": subscription.migration_target_vlan
                    })
                except Exception as e:
                    migration_results[interface["interface_id"]]["netbox_error"] = str(e)
    
    subscription.migration_results = migration_results
    subscription.interfaces_migrated = len([r for r in migration_results.values() if r["success"]])
    subscription.migration_completed = True
    
    return subscription


@delete_vlan.step("Remove VLAN from Devices")
async def remove_vlan_from_devices(subscription: VLANProvisioning) -> State:
    """Remove VLAN configuration from all network devices using centralized API management"""
    
    # Get unique devices that have this VLAN
    unique_devices = set()
    for interface in subscription.vlan_dependencies["interfaces"]:
        unique_devices.add(interface["device_id"])
    
    # Deploy using centralized API management with optimal connection methods
    deployment_config = {
        "vlan_id": subscription.vlan_id,
        "vlan_name": subscription.vlan_name,
        "operation": "remove",
        "force_remove": subscription.force_delete,
        "cleanup_interfaces": not subscription.migrate_interfaces
    }
    
    removal_results = await device_connector.deploy_to_devices_async(
        device_ids=list(unique_devices),
        config_type="vlan_removal",
        config_data=deployment_config,
        max_concurrent=3  # Limit concurrent removals for safety
    )
    
    # Process results for subscription
    processed_results = {}
    for device_id, result in removal_results.items():
        processed_results[device_id] = {
            "success": result.get("success", False),
            "error": result.get("error"),
            "device_name": result.get("device_name"),
            "interfaces_cleaned": result.get("interfaces_cleaned", 0),
            "svi_removed": result.get("svi_removed", False),
            "connection_method": result.get("connection_method")
        }
    
    subscription.removal_results = processed_results
    subscription.devices_updated = len([r for r in processed_results.values() if r["success"]])
    subscription.vlan_removed_from_devices = True
    
    return subscription


@delete_vlan.step("Cleanup IP Resources")
def cleanup_ip_resources(subscription: VLANProvisioning) -> State:
    """Cleanup IP addresses and subnets associated with VLAN"""
    
    if not subscription.cleanup_ip_addresses:
        subscription.ip_cleanup_skipped = True
        return subscription
    
    ip_cleanup_results = {
        "ip_addresses_deleted": 0,
        "subnets_deleted": 0,
        "errors": []
    }
    
    # Delete IP addresses
    for ip_addr in subscription.vlan_dependencies["ip_addresses"]:
        try:
            # Only delete unassigned or if force delete
            if ip_addr["status"] != "active" or subscription.force_delete:
                netbox.delete_ip_address(ip_addr["ip_id"])
                ip_cleanup_results["ip_addresses_deleted"] += 1
        except Exception as e:
            ip_cleanup_results["errors"].append(f"Failed to delete IP {ip_addr['address']}: {str(e)}")
    
    # Delete associated subnets
    for subnet in subscription.associated_subnets:
        try:
            # Check if subnet has remaining IPs
            remaining_ips = netbox.get_subnet_ip_addresses(subnet["id"])
            if not remaining_ips or subscription.force_delete:
                netbox.delete_subnet(subnet["id"])
                ip_cleanup_results["subnets_deleted"] += 1
        except Exception as e:
            ip_cleanup_results["errors"].append(f"Failed to delete subnet {subnet['prefix']}: {str(e)}")
    
    subscription.ip_cleanup_results = ip_cleanup_results
    subscription.ip_resources_cleaned = True
    
    return subscription


@delete_vlan.step("Cleanup DHCP Resources")
def cleanup_dhcp_resources(subscription: VLANProvisioning) -> State:
    """Cleanup DHCP pools and scopes"""
    
    if not subscription.cleanup_dhcp_pools:
        subscription.dhcp_cleanup_skipped = True
        return subscription
    
    dhcp_cleanup_results = {
        "pools_deleted": 0,
        "errors": []
    }
    
    for dhcp_pool in subscription.vlan_dependencies["dhcp_pools"]:
        try:
            # Remove DHCP pool configuration
            cleanup_result = execute_playbook(
                "ansible/operations/cleanup_dhcp_pool.yaml",
                extra_vars={
                    "dhcp_server": dhcp_pool.get("server_ip"),
                    "pool_name": dhcp_pool.get("name"),
                    "vlan_id": subscription.vlan_id,
                    "force_delete": subscription.force_delete
                }
            )
            
            if cleanup_result.get("success"):
                dhcp_cleanup_results["pools_deleted"] += 1
            else:
                dhcp_cleanup_results["errors"].append(f"Failed to delete DHCP pool {dhcp_pool.get('name')}")
                
        except Exception as e:
            dhcp_cleanup_results["errors"].append(f"Failed to cleanup DHCP pool {dhcp_pool.get('name')}: {str(e)}")
    
    subscription.dhcp_cleanup_results = dhcp_cleanup_results
    subscription.dhcp_resources_cleaned = True
    
    return subscription


@delete_vlan.step("Cleanup Routing Resources")
def cleanup_routing_resources(subscription: VLANProvisioning) -> State:
    """Cleanup routing table entries"""
    
    if not subscription.cleanup_routing_entries:
        subscription.routing_cleanup_skipped = True
        return subscription
    
    routing_cleanup_results = {
        "routes_deleted": 0,
        "errors": []
    }
    
    # Group routes by device for efficient cleanup
    device_routes = {}
    for route in subscription.vlan_dependencies["routes"]:
        device_id = route.get("device_id")
        if device_id not in device_routes:
            device_routes[device_id] = []
        device_routes[device_id].append(route)
    
    for device_id, routes in device_routes.items():
        device_info = netbox.get_device(device_id)
        device_ip = device_info.get("primary_ip4", {}).get("address", "").split("/")[0]
        
        if device_ip:
            try:
                cleanup_result = execute_playbook(
                    "ansible/operations/cleanup_vlan_routes.yaml",
                    extra_vars={
                        "device_ip": device_ip,
                        "device_platform": device_info.get("platform", {}).get("slug"),
                        "vlan_id": subscription.vlan_id,
                        "routes_to_delete": [r["prefix"] for r in routes],
                        "force_delete": subscription.force_delete
                    }
                )
                
                if cleanup_result.get("success"):
                    routing_cleanup_results["routes_deleted"] += cleanup_result.get("routes_deleted", 0)
                else:
                    routing_cleanup_results["errors"].append(f"Failed to cleanup routes on {device_info.get('name')}")
                    
            except Exception as e:
                routing_cleanup_results["errors"].append(f"Failed to cleanup routes on {device_info.get('name')}: {str(e)}")
    
    subscription.routing_cleanup_results = routing_cleanup_results
    subscription.routing_resources_cleaned = True
    
    return subscription


@delete_vlan.step("Update NetBox Records")
def update_netbox_records(subscription: VLANProvisioning) -> State:
    """Update NetBox records and delete VLAN"""
    
    try:
        # Remove VLAN from interface associations that weren't migrated
        for interface in subscription.vlan_dependencies["interfaces"]:
            if not subscription.migrate_interfaces or interface["interface_id"] not in subscription.migration_results:
                interface_update = {}
                
                # Remove from untagged VLAN
                if interface.get("untagged_vlan"):
                    interface_update["untagged_vlan"] = None
                
                # Remove from tagged VLANs
                if interface.get("tagged_vlans"):
                    current_tagged = netbox.get_interface(interface["interface_id"]).get("tagged_vlans", [])
                    updated_tagged = [v for v in current_tagged if v.get("vid") != subscription.vlan_id]
                    interface_update["tagged_vlans"] = [v["id"] for v in updated_tagged]
                
                if interface_update:
                    netbox.update_interface(interface["interface_id"], interface_update)
        
        # Delete the VLAN from NetBox
        netbox.delete_vlan(subscription.vlan_id)
        
        subscription.netbox_updated = True
        subscription.vlan_deleted_from_netbox = True
        
    except Exception as e:
        subscription.netbox_error = str(e)
        subscription.netbox_updated = False
    
    # Create deletion summary
    subscription.deletion_summary = {
        "vlan_id": subscription.vlan_id,
        "vlan_name": subscription.vlan_name,
        "dependencies_found": subscription.total_dependencies,
        "interfaces_affected": len(subscription.vlan_dependencies["interfaces"]),
        "interfaces_migrated": subscription.interfaces_migrated if subscription.migrate_interfaces else 0,
        "devices_updated": subscription.devices_updated,
        "ip_addresses_deleted": subscription.ip_cleanup_results.get("ip_addresses_deleted", 0) if subscription.cleanup_ip_addresses else 0,
        "subnets_deleted": subscription.ip_cleanup_results.get("subnets_deleted", 0) if subscription.cleanup_ip_addresses else 0,
        "dhcp_pools_deleted": subscription.dhcp_cleanup_results.get("pools_deleted", 0) if subscription.cleanup_dhcp_pools else 0,
        "routes_deleted": subscription.routing_cleanup_results.get("routes_deleted", 0) if subscription.cleanup_routing_entries else 0,
        "force_delete_used": subscription.force_delete,
        "backup_created": subscription.config_backed_up
    }
    
    return subscription
