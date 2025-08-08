"""
VLAN Management Workflow
Create, modify, and manage VLANs across network infrastructure
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
from typing import List, Optional

from products.product_types.vlan import VlanInactive, VlanProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from services.api_manager import api_manager
from services.device_connector import device_connector
from workflows.shared import device_selector


class CreateVlanForm(FormPage):
    """VLAN creation form"""
    vlan_id: int = Field(
        description="VLAN ID (1-4094)",
        ge=1,
        le=4094
    )
    vlan_name: str = Field(
        description="VLAN Name",
        min_length=1,
        max_length=32
    )
    description: str = Field(
        description="VLAN Description",
        default=""
    )
    deployment_scope: Choice = Field(
        description="Deployment Scope",
        choices=[
            ("single_device", "Single Device"),
            ("device_group", "Device Group"),
            ("site_devices", "Site Devices"), 
            ("all_switches", "All Switches")
        ],
        default="single_device"
    )
    target_devices: List[str] = Field(
        description="Target Device IDs (if single/group)",
        default=[]
    )
    site_name: str = Field(
        description="Site Name (if site deployment)",
        required=False
    )
    vlan_type: Choice = Field(
        description="VLAN Type",
        choices=[
            ("data", "Data VLAN"),
            ("voice", "Voice VLAN"),
            ("management", "Management VLAN"),
            ("guest", "Guest VLAN"),
            ("dmz", "DMZ VLAN"),
            ("native", "Native VLAN")
        ],
        default="data"
    )
    ip_network: str = Field(
        description="Associated IP Network (CIDR)",
        required=False
    )
    enable_dhcp: bool = Field(
        description="Enable DHCP Helper",
        default=False
    )
    dhcp_server: str = Field(
        description="DHCP Server IP",
        required=False
    )
    trunk_allowed: bool = Field(
        description="Allow on Trunk Ports",
        default=True
    )

    @validator('vlan_id')
    def validate_vlan_id(cls, v):
        reserved_vlans = [1, 1002, 1003, 1004, 1005]  # Common reserved VLANs
        if v in reserved_vlans:
            raise ValueError(f'VLAN {v} is reserved')
        return v


class ModifyVlanForm(FormPage):
    """VLAN modification form"""
    vlan_id: int = Field(description="Existing VLAN ID to modify")
    new_name: str = Field(description="New VLAN Name", required=False)
    new_description: str = Field(description="New Description", required=False)
    add_to_devices: List[str] = Field(description="Add to Devices", default=[])
    remove_from_devices: List[str] = Field(description="Remove from Devices", default=[])
    modify_trunk_config: bool = Field(description="Modify Trunk Configuration", default=False)


@workflow("Create VLAN", target=Target.CREATE)
def create_vlan() -> StepList:
    return begin
        >> store_process_subscription(Target.CREATE)
        >> validate_vlan_availability
        >> select_target_devices
        >> create_netbox_vlan
        >> deploy_vlan_configuration
        >> configure_ip_services
        >> verify_vlan_deployment
        >> done


@workflow("Modify VLAN", target=Target.MODIFY)
def modify_vlan() -> StepList:
    return begin
        >> store_process_subscription(Target.MODIFY)
        >> validate_vlan_exists
        >> plan_vlan_changes
        >> update_netbox_vlan
        >> deploy_vlan_changes
        >> verify_vlan_modification
        >> done


def initial_input_form_generator(subscription_id: UUIDstr) -> FormPage:
    """Generate VLAN creation form"""
    return CreateVlanForm


def validate_vlan_availability(subscription: VlanInactive) -> VlanProvisioning:
    """Validate VLAN ID is available across target devices"""
    subscription = VlanProvisioning.from_other_lifecycle(
        subscription, SubscriptionLifecycle.PROVISIONING
    )
    
    # Check VLAN availability in NetBox
    existing_vlan = netbox.get_vlan_by_id(subscription.vlan_id)
    if existing_vlan:
        raise ValueError(f"VLAN {subscription.vlan_id} already exists in NetBox")
    
    # Check VLAN availability on target devices
    callback_route = f"/api/workflows/vlan/create/{subscription.subscription_id}/validate"
    
    extra_vars = {
        "vlan_id": subscription.vlan_id,
        "check_availability": True
    }
    
    execute_playbook(
        playbook_name="validate_vlan_availability.yaml",
        callback_route=callback_route,
        inventory="placeholder\n",  # Will be replaced in next step
        extra_vars=extra_vars
    )
    
    return subscription


def select_target_devices(subscription: VlanProvisioning) -> VlanProvisioning:
    """Select target devices based on deployment scope"""
    
    target_devices = []
    
    if subscription.deployment_scope == "single_device":
        target_devices = subscription.target_devices
    
    elif subscription.deployment_scope == "device_group":
        # Get devices from specified group
        target_devices = subscription.target_devices
    
    elif subscription.deployment_scope == "site_devices":
        # Get all switches in site
        site_devices = netbox.get_devices_by_site(
            site=subscription.site_name,
            device_role="switch"
        )
        target_devices = [d["id"] for d in site_devices]
    
    elif subscription.deployment_scope == "all_switches":
        # Get all switches in network
        all_switches = netbox.get_devices_by_role("switch", status="active")
        target_devices = [d["id"] for d in all_switches]
    
    subscription.target_device_ids = target_devices
    subscription.device_count = len(target_devices)
    
    return subscription


def create_netbox_vlan(subscription: VlanProvisioning) -> VlanProvisioning:
    """Create VLAN record in NetBox IPAM"""
    
    vlan_payload = {
        "vid": subscription.vlan_id,
        "name": subscription.vlan_name,
        "description": subscription.description,
        "status": "active",
        "role": subscription.vlan_type,
        "custom_fields": {
            "deployment_scope": subscription.deployment_scope,
            "created_by_orchestrator": True,
            "trunk_allowed": subscription.trunk_allowed
        }
    }
    
    # Create VLAN in NetBox
    vlan_netbox_id = netbox.create_vlan(vlan_payload)
    subscription.netbox_vlan_id = vlan_netbox_id
    
    # Create associated IP network if specified
    if subscription.ip_network:
        prefix_payload = {
            "prefix": subscription.ip_network,
            "description": f"Network for VLAN {subscription.vlan_id} - {subscription.vlan_name}",
            "vlan": vlan_netbox_id,
            "status": "active",
            "is_pool": False
        }
        
        prefix_id = netbox.create_prefix(prefix_payload)
        subscription.netbox_prefix_id = prefix_id
    
    return subscription


def deploy_vlan_configuration(subscription: VlanProvisioning) -> VlanProvisioning:
    """Deploy VLAN configuration to target devices"""
    
    # Get device details for inventory
    devices = []
    for device_id in subscription.target_device_ids:
        device = netbox.get_device(device_id)
        devices.append({
            "id": device_id,
            "name": device["name"],
            "ip": device.get("primary_ip4", device["name"]),
            "platform": device.get("platform", "unknown")
        })
    
    # Build inventory
    inventory_hosts = [d["ip"] for d in devices]
    inventory = "\n".join(inventory_hosts) + "\n"
    
    callback_route = f"/api/workflows/vlan/create/{subscription.subscription_id}/deploy"
    
    extra_vars = {
        "vlan_id": subscription.vlan_id,
        "vlan_name": subscription.vlan_name,
        "vlan_description": subscription.description,
        "vlan_type": subscription.vlan_type,
        "trunk_allowed": subscription.trunk_allowed,
        "devices": devices
    }
    
    execute_playbook(
        playbook_name="deploy_vlan_configuration.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=extra_vars
    )
    
    return subscription


def configure_ip_services(subscription: VlanProvisioning) -> VlanProvisioning:
    """Configure IP services for VLAN (DHCP, SVI)"""
    
    if not (subscription.enable_dhcp or subscription.ip_network):
        return subscription
    
    callback_route = f"/api/workflows/vlan/create/{subscription.subscription_id}/ip_services"
    
    # Configure on gateway/core devices
    core_devices = netbox.get_devices_by_role("core", status="active")
    core_inventory = "\n".join([d.get("primary_ip4", d["name"]) for d in core_devices]) + "\n"
    
    extra_vars = {
        "vlan_id": subscription.vlan_id,
        "vlan_name": subscription.vlan_name,
        "ip_network": subscription.ip_network,
        "enable_dhcp": subscription.enable_dhcp,
        "dhcp_server": subscription.dhcp_server,
        "create_svi": subscription.ip_network is not None
    }
    
    execute_playbook(
        playbook_name="configure_vlan_ip_services.yaml",
        callback_route=callback_route,
        inventory=core_inventory,
        extra_vars=extra_vars
    )
    
    return subscription


def verify_vlan_deployment(subscription: VlanProvisioning) -> VlanProvisioning:
    """Verify VLAN was deployed successfully"""
    
    callback_route = f"/api/workflows/vlan/create/{subscription.subscription_id}/verify"
    
    # Get device inventory
    devices = []
    for device_id in subscription.target_device_ids:
        device = netbox.get_device(device_id)
        devices.append(device.get("primary_ip4", device["name"]))
    
    inventory = "\n".join(devices) + "\n"
    
    extra_vars = {
        "vlan_id": subscription.vlan_id,
        "expected_device_count": subscription.device_count
    }
    
    execute_playbook(
        playbook_name="verify_vlan_deployment.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=extra_vars
    )
    
    return subscription


# VLAN MODIFICATION WORKFLOW STEPS

def validate_vlan_exists(subscription: VlanInactive) -> VlanProvisioning:
    """Validate VLAN exists before modification"""
    subscription = VlanProvisioning.from_other_lifecycle(
        subscription, SubscriptionLifecycle.PROVISIONING
    )
    
    existing_vlan = netbox.get_vlan_by_id(subscription.vlan_id)
    if not existing_vlan:
        raise ValueError(f"VLAN {subscription.vlan_id} does not exist")
    
    subscription.current_vlan_config = existing_vlan
    return subscription


def plan_vlan_changes(subscription: VlanProvisioning) -> VlanProvisioning:
    """Plan VLAN configuration changes"""
    
    change_plan = {
        "name_change": subscription.new_name != subscription.current_vlan_config.get("name"),
        "description_change": subscription.new_description != subscription.current_vlan_config.get("description"),
        "device_additions": subscription.add_to_devices,
        "device_removals": subscription.remove_from_devices,
        "trunk_config_change": subscription.modify_trunk_config
    }
    
    subscription.change_plan = change_plan
    return subscription


def update_netbox_vlan(subscription: VlanProvisioning) -> VlanProvisioning:
    """Update VLAN record in NetBox"""
    
    update_payload = {}
    
    if subscription.change_plan["name_change"]:
        update_payload["name"] = subscription.new_name
    
    if subscription.change_plan["description_change"]:
        update_payload["description"] = subscription.new_description
    
    if update_payload:
        netbox.update_vlan(subscription.netbox_vlan_id, update_payload)
    
    return subscription


def deploy_vlan_changes(subscription: VlanProvisioning) -> VlanProvisioning:
    """Deploy VLAN configuration changes to devices"""
    
    # Combine all affected devices
    affected_devices = list(set(
        subscription.add_to_devices + 
        subscription.remove_from_devices
    ))
    
    if not affected_devices:
        return subscription
    
    callback_route = f"/api/workflows/vlan/modify/{subscription.subscription_id}/deploy"
    
    inventory = "\n".join(affected_devices) + "\n"
    
    extra_vars = {
        "vlan_id": subscription.vlan_id,
        "change_plan": subscription.change_plan,
        "new_name": subscription.new_name,
        "new_description": subscription.new_description,
        "add_to_devices": subscription.add_to_devices,
        "remove_from_devices": subscription.remove_from_devices
    }
    
    execute_playbook(
        playbook_name="modify_vlan_configuration.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=extra_vars
    )
    
    return subscription


def verify_vlan_modification(subscription: VlanProvisioning) -> VlanProvisioning:
    """Verify VLAN modifications were applied successfully"""
    
    callback_route = f"/api/workflows/vlan/modify/{subscription.subscription_id}/verify"
    
    # Get all affected devices
    affected_devices = list(set(
        subscription.add_to_devices + 
        subscription.remove_from_devices
    ))
    
    inventory = "\n".join(affected_devices) + "\n"
    
    extra_vars = {
        "vlan_id": subscription.vlan_id,
        "change_plan": subscription.change_plan,
        "verification_timestamp": subscription.created_at.isoformat()
    }
    
    execute_playbook(
        playbook_name="verify_vlan_modification.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=extra_vars
    )
    
    return subscription
