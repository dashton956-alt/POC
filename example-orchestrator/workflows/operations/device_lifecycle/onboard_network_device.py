"""
Network Device Onboarding Workflow
Complete device provisioning and configuration setup
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

from products.product_types.device import DeviceInactive, DeviceProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from services.api_manager import api_manager
from services.device_connector import device_connector
from workflows.shared import node_selector


class DeviceOnboardingForm(FormPage):
    """Device onboarding configuration"""
    device_ip: str = Field(description="Device Management IP Address")
    device_hostname: str = Field(description="Device Hostname")
    device_type: Choice = Field(
        description="Device Type",
        choices=[
            ("cisco_catalyst_9300", "Cisco Catalyst 9300"),
            ("cisco_catalyst_9200", "Cisco Catalyst 9200"),
            ("cisco_nexus_9000", "Cisco Nexus 9000"),
            ("juniper_ex4300", "Juniper EX4300"),
            ("arista_7050sx3", "Arista 7050SX3")
        ]
    )
    site_location: str = Field(description="Site/Location", default="default-site")
    device_role: Choice = Field(
        description="Device Role",
        choices=[
            ("access_switch", "Access Switch"),
            ("distribution_switch", "Distribution Switch"),
            ("core_switch", "Core Switch"),
            ("router", "Router"),
            ("firewall", "Firewall")
        ]
    )
    management_vlan: int = Field(
        description="Management VLAN ID", 
        default=1
    )
    snmp_community: str = Field(
        description="SNMP Community String",
        default="public"
    )
    ssh_username: str = Field(description="SSH Username")
    ssh_password: str = Field(description="SSH Password", password=True)
    enable_monitoring: bool = Field(
        description="Enable SNMP Monitoring",
        default=True
    )
    apply_base_config: bool = Field(
        description="Apply base configuration template",
        default=True
    )


@workflow("Onboard Network Device", target=Target.CREATE)
def onboard_network_device() -> StepList:
    return begin
        >> store_process_subscription(Target.CREATE)
        >> validate_device_connectivity
        >> create_netbox_device
        >> apply_base_configuration
        >> setup_monitoring
        >> register_with_oss
        >> done


def initial_input_form_generator(subscription_id: UUIDstr) -> FormPage:
    """Generate the device onboarding form"""
    return DeviceOnboardingForm


def validate_device_connectivity(subscription: DeviceInactive) -> DeviceProvisioning:
    """Validate device is reachable and gather basic information"""
    subscription = DeviceProvisioning.from_other_lifecycle(
        subscription, SubscriptionLifecycle.PROVISIONING
    )
    
    # Execute connectivity validation playbook
    callback_route = f"/api/workflows/device/onboarding/{subscription.subscription_id}/validate"
    
    extra_vars = {
        "device_ip": subscription.device_ip,
        "ssh_username": subscription.ssh_username, 
        "ssh_password": subscription.ssh_password,
        "snmp_community": subscription.snmp_community
    }
    
    execute_playbook(
        playbook_name="validate_device_connectivity.yaml",
        callback_route=callback_route,
        inventory=f"{subscription.device_ip}\n",
        extra_vars=extra_vars
    )
    
    return subscription


def create_netbox_device(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Create comprehensive device record in NetBox"""
    
    # Get device details from connectivity validation
    device_info = subscription.validation_results
    
    device_payload = {
        "name": subscription.device_hostname,
        "device_type": subscription.device_type,
        "device_role": subscription.device_role,
        "site": subscription.site_location,
        "serial": device_info.get("serial_number"),
        "primary_ip4": subscription.device_ip,
        "status": "active",
        "platform": device_info.get("platform"),
        "custom_fields": {
            "management_vlan": subscription.management_vlan,
            "onboarded_date": subscription.created_at.isoformat(),
            "ssh_username": subscription.ssh_username,
            "snmp_community": subscription.snmp_community,
            "monitoring_enabled": subscription.enable_monitoring
        }
    }
    
    # Create device in NetBox
    device_id = netbox.create_device(device_payload)
    subscription.netbox_device_id = device_id
    
    # Create device interfaces based on discovery
    interfaces = device_info.get("interfaces", [])
    for interface in interfaces:
        interface_payload = {
            "device": device_id,
            "name": interface["name"],
            "type": interface["type"],
            "enabled": interface.get("enabled", False),
            "speed": interface.get("speed"),
            "duplex": interface.get("duplex"),
            "description": interface.get("description", "")
        }
        netbox.create_interface(interface_payload)
    
    return subscription


def apply_base_configuration(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Apply base device configuration template"""
    
    if not subscription.apply_base_config:
        return subscription
    
    callback_route = f"/api/workflows/device/onboarding/{subscription.subscription_id}/configure"
    
    extra_vars = {
        "device_hostname": subscription.device_hostname,
        "device_ip": subscription.device_ip,
        "device_type": subscription.device_type,
        "site_location": subscription.site_location,
        "management_vlan": subscription.management_vlan,
        "snmp_community": subscription.snmp_community,
        "ssh_username": subscription.ssh_username,
        "ssh_password": subscription.ssh_password
    }
    
    execute_playbook(
        playbook_name="apply_base_device_config.yaml",
        callback_route=callback_route,
        inventory=f"{subscription.device_ip}\n",
        extra_vars=extra_vars
    )
    
    return subscription


def setup_monitoring(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Configure device monitoring and alerting"""
    
    if not subscription.enable_monitoring:
        return subscription
    
    callback_route = f"/api/workflows/device/onboarding/{subscription.subscription_id}/monitoring"
    
    extra_vars = {
        "device_ip": subscription.device_ip,
        "device_hostname": subscription.device_hostname,
        "snmp_community": subscription.snmp_community,
        "device_type": subscription.device_type
    }
    
    execute_playbook(
        playbook_name="setup_device_monitoring.yaml",
        callback_route=callback_route,
        inventory="monitoring-server\n",
        extra_vars=extra_vars
    )
    
    return subscription


def register_with_oss(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Register device with external OSS systems"""
    
    # Register with Catalyst Center (if applicable)
    if subscription.device_type.startswith("cisco_"):
        callback_route = f"/api/workflows/device/onboarding/{subscription.subscription_id}/catalyst"
        
        extra_vars = {
            "device_ip": subscription.device_ip,
            "device_hostname": subscription.device_hostname,
            "site_location": subscription.site_location,
            "credentials": {
                "username": subscription.ssh_username,
                "password": subscription.ssh_password
            }
        }
        
        execute_playbook(
            playbook_name="register_catalyst_center.yaml",
            callback_route=callback_route,
            inventory="catalyst-center\n",
            extra_vars=extra_vars
        )
    
    # Register with ITSM (ServiceNow)
    itsm_payload = {
        "device_name": subscription.device_hostname,
        "ip_address": subscription.device_ip,
        "location": subscription.site_location,
        "device_type": subscription.device_type,
        "status": "operational",
        "onboarded_date": subscription.created_at.isoformat()
    }
    
    # Would integrate with ServiceNow API here
    subscription.itsm_registered = True
    
    return subscription
