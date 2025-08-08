"""
Network Device Discovery Workflow
Auto-discover devices via SNMP, LLDP, CDP and create inventory records
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


class DiscoveryTargetForm(FormPage):
    """Target network for device discovery"""
    target_network: str = Field(
        description="Network range to scan (e.g., 192.168.1.0/24)"
    )
    discovery_method: Choice = Field(
        description="Discovery method",
        choices=[
            ("snmp", "SNMP Discovery"),
            ("lldp", "LLDP Discovery"), 
            ("cdp", "CDP Discovery"),
            ("ping_sweep", "Ping Sweep + SNMP"),
            ("nmap", "Network Map Scan")
        ],
        default="snmp"
    )
    snmp_community: str = Field(
        description="SNMP Community String",
        default="public"
    )
    discovery_timeout: int = Field(
        description="Discovery timeout in seconds",
        default=60
    )
    auto_onboard: bool = Field(
        description="Automatically onboard discovered devices",
        default=False
    )


@workflow("Discover Network Device", target=Target.CREATE)
def discover_network_device() -> StepList:
    return begin
        >> store_process_subscription(Target.CREATE)
        >> start_network_discovery
        >> process_discovery_results
        >> create_device_inventory
        >> done


def initial_input_form_generator(subscription_id: UUIDstr) -> FormPage:
    """Generate the initial discovery form"""
    return DiscoveryTargetForm


def start_network_discovery(subscription: DeviceInactive) -> DeviceProvisioning:
    """Initiate network discovery scan"""
    subscription = DeviceProvisioning.from_other_lifecycle(
        subscription, SubscriptionLifecycle.PROVISIONING
    )
    
    # Execute discovery playbook
    callback_route = f"/api/workflows/device/discovery/{subscription.subscription_id}/callback"
    
    # Prepare discovery parameters
    extra_vars = {
        "target_network": subscription.target_network,
        "discovery_method": subscription.discovery_method,
        "snmp_community": subscription.snmp_community,
        "discovery_timeout": subscription.discovery_timeout
    }
    
    execute_playbook(
        playbook_name="device_discovery.yaml",
        callback_route=callback_route,
        inventory="localhost\n",  # Run on orchestrator host
        extra_vars=extra_vars
    )
    
    return subscription


def process_discovery_results(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Process discovery results and validate devices"""
    # Discovery results would be received via callback
    # For now, simulate discovery results
    discovery_results = [
        {
            "ip_address": "192.168.1.10",
            "hostname": "switch-01.local",
            "device_type": "Cisco Catalyst 9300",
            "serial": "FCW2140L0GH",
            "mac_address": "00:1B:0D:63:C2:26",
            "snmp_sysname": "switch-01",
            "os_version": "16.12.04"
        },
        {
            "ip_address": "192.168.1.11", 
            "hostname": "switch-02.local",
            "device_type": "Cisco Catalyst 9300",
            "serial": "FCW2140L0GI",
            "mac_address": "00:1B:0D:63:C2:27",
            "snmp_sysname": "switch-02",
            "os_version": "16.12.04"
        }
    ]
    
    subscription.discovery_results = discovery_results
    subscription.devices_found = len(discovery_results)
    
    return subscription


def create_device_inventory(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Create device records in NetBox inventory"""
    created_devices = []
    
    for device_data in subscription.discovery_results:
        # Create device in NetBox
        device_payload = {
            "name": device_data["hostname"],
            "device_type": device_data["device_type"],
            "serial": device_data["serial"],
            "primary_ip4": device_data["ip_address"],
            "site": "default-site",  # Configure based on discovery
            "status": "discovered",
            "custom_fields": {
                "discovery_method": subscription.discovery_method,
                "discovery_date": subscription.created_at.isoformat(),
                "auto_discovered": True
            }
        }
        
        # Create in NetBox (mock for now)
        device_id = netbox.create_device(device_payload)
        
        created_devices.append({
            "netbox_id": device_id,
            "hostname": device_data["hostname"],
            "ip_address": device_data["ip_address"],
            "serial": device_data["serial"]
        })
    
    subscription.created_devices = created_devices
    subscription.inventory_created = True
    
    # If auto_onboard is enabled, trigger onboarding workflows
    if subscription.auto_onboard:
        for device in created_devices:
            # Trigger device onboarding workflow
            pass  # Would trigger onboard_network_device workflow
    
    return subscription
