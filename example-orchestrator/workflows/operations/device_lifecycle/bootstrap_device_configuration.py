"""
Bootstrap Device Configuration Workflow
Apply initial day-0 configuration to network devices
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

from products.product_types.device import DeviceInactive, DeviceProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from services.api_manager import api_manager, get_device_connection
from services.device_connector import device_connection_manager, connect_to_device, deploy_device_configuration, execute_device_command
from workflows.shared import device_selector, site_selector


class BootstrapConfigurationForm(FormPage):
    """Bootstrap Configuration Form - NetBox Integrated"""
    
    # Device Selection - NetBox driven
    target_device: str = Field(
        description="Target Device to Bootstrap",
        choices=get_unbootstrapped_devices_from_netbox()
    )
    
    # Site Context for Configuration
    site_context: str = Field(
        description="Site (determines local settings)",
        choices=get_sites_from_netbox(),
        default=""
    )
    
    # Configuration Template Selection - Role-based
    config_template: Choice = Field(
        description="Configuration Template (auto-suggested by device role)",
        choices=get_templates_by_device_role_from_netbox()
    )
    
    # Management Configuration - NetBox IP integration
    mgmt_ip: str = Field(
        description="Management IP Address (from NetBox IPAM)",
        choices=get_available_mgmt_ips_from_netbox(),
        regex=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    )
    mgmt_subnet_mask: str = Field(
        description="Management Subnet Mask (auto-detected from NetBox)",
        regex=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
        default=get_mgmt_subnet_mask_from_netbox()
    )
    mgmt_gateway: str = Field(
        description="Management Gateway (from NetBox prefix)",
        regex=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
        default=get_mgmt_gateway_from_netbox()
    )
    
    # DNS Configuration - Site-based defaults
    primary_dns: str = Field(
        description="Primary DNS Server (site default from NetBox)",
        regex=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
        default=get_site_primary_dns_from_netbox()
    )
    secondary_dns: str = Field(
        description="Secondary DNS Server (site default from NetBox)",
        regex=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
        default=get_site_secondary_dns_from_netbox()
    )
    domain_name: str = Field(
        description="Domain Name (from site configuration)",
        default=get_site_domain_from_netbox()
    )
    
    # NTP Configuration - Site-based
    ntp_server: str = Field(
        description="NTP Server (site default from NetBox)",
        default=get_site_ntp_server_from_netbox()
    )
    timezone: Choice = Field(
        description="Timezone (from site location)",
        choices=get_timezone_choices(),
        default=get_site_timezone_from_netbox()
    )
    
    # SNMP Configuration - Security policy based
    snmp_community: str = Field(
        description="SNMP Community String (from NetBox secrets)",
        default=get_snmp_community_from_netbox()
    )
    snmp_location: str = Field(
        description="SNMP Location (from site information)",
        default=get_snmp_location_from_netbox()
    )
    )
    snmp_contact: str = Field(
        description="SNMP Contact",
        default=""
    )
    
    # Advanced Options
    enable_ssh: bool = Field(
        description="Enable SSH",
        default=True
    )
    enable_https: bool = Field(
        description="Enable HTTPS Management",
        default=True
    )
    logging_server: Optional[str] = Field(
        description="Syslog Server IP (Optional)",
        regex=r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$',
        default=None
    )


@workflow("Bootstrap Device Configuration", target=Target.CREATE)
def bootstrap_device_configuration(subscription: DeviceInactive) -> State:
    """Bootstrap device configuration workflow"""
    return (
        begin
        >> store_process_subscription(subscription)
        >> collect_bootstrap_configuration
        >> validate_device_reachability
        >> generate_bootstrap_config
        >> apply_bootstrap_config
        >> verify_bootstrap_config
        >> setup_monitoring
        >> register_in_netbox
        >> done
    )


@bootstrap_device_configuration.step("Collect Bootstrap Configuration")
def collect_bootstrap_configuration(subscription: DeviceProvisioning) -> State:
    """Collect bootstrap configuration requirements"""
    
    # Get device information from NetBox
    device_info = netbox.get_device(subscription.device_id)
    
    # Determine device platform and capabilities
    platform = device_info.get("platform", {}).get("slug", "unknown")
    vendor = device_info.get("device_type", {}).get("manufacturer", {}).get("slug", "unknown")
    
    # Validate template compatibility
    template_compatibility = {
        "cisco": ["core_switch", "distribution_switch", "access_switch", "router"],
        "juniper": ["core_switch", "distribution_switch", "access_switch", "router"],
        "arista": ["core_switch", "distribution_switch", "access_switch"],
        "fortinet": ["firewall"],
        "palo_alto": ["firewall"]
    }
    
    compatible_templates = template_compatibility.get(vendor, ["custom"])
    if subscription.config_template not in compatible_templates:
        raise ValueError(f"Template {subscription.config_template} not compatible with {vendor} devices")
    
    subscription.device_platform = platform
    subscription.device_vendor = vendor
    subscription.compatible_templates = compatible_templates
    
    return subscription


@bootstrap_device_configuration.step("Validate Device Reachability")
def validate_device_reachability(subscription: DeviceProvisioning) -> State:
    """Validate device is reachable for configuration"""
    
    device_ip = subscription.mgmt_ip
    
    # Test basic connectivity
    ping_result = execute_playbook(
        "ansible/operations/validate_device_connectivity.yaml",
        extra_vars={
            "target_hosts": [device_ip],
            "connection_timeout": 30
        }
    )
    
    if not ping_result.get("success"):
        raise RuntimeError(f"Device {device_ip} is not reachable: {ping_result.get('error')}")
    
    # Test device access
    access_result = execute_playbook(
        "ansible/operations/test_device_access.yaml",
        extra_vars={
            "device_ip": device_ip,
            "device_platform": subscription.device_platform,
            "test_protocols": ["ssh", "telnet", "console"]
        }
    )
    
    subscription.access_method = access_result.get("available_protocols", ["console"])[0]
    subscription.device_reachable = True
    
    return subscription


@bootstrap_device_configuration.step("Generate Bootstrap Configuration")
def generate_bootstrap_config(subscription: DeviceProvisioning) -> State:
    """Generate device-specific bootstrap configuration"""
    
    # Template variables
    template_vars = {
        "device_hostname": subscription.device_name or f"device-{subscription.device_id}",
        "mgmt_ip": subscription.mgmt_ip,
        "mgmt_subnet_mask": subscription.mgmt_subnet_mask,
        "mgmt_gateway": subscription.mgmt_gateway,
        "primary_dns": subscription.primary_dns,
        "secondary_dns": subscription.secondary_dns,
        "domain_name": subscription.domain_name,
        "ntp_server": subscription.ntp_server,
        "timezone": subscription.timezone,
        "snmp_community": subscription.snmp_community,
        "snmp_location": subscription.snmp_location,
        "snmp_contact": subscription.snmp_contact,
        "enable_ssh": subscription.enable_ssh,
        "enable_https": subscription.enable_https,
        "logging_server": subscription.logging_server,
        "device_platform": subscription.device_platform,
        "device_vendor": subscription.device_vendor
    }
    
    # Generate configuration using Ansible template
    config_result = execute_playbook(
        "ansible/operations/generate_bootstrap_config.yaml",
        extra_vars={
            "template_name": subscription.config_template,
            "template_vars": template_vars,
            "output_format": subscription.device_platform
        }
    )
    
    if not config_result.get("success"):
        raise RuntimeError(f"Failed to generate bootstrap configuration: {config_result.get('error')}")
    
    subscription.generated_config = config_result.get("configuration")
    subscription.config_checksum = config_result.get("checksum")
    
    return subscription


@bootstrap_device_configuration.step("Apply Bootstrap Configuration")
def apply_bootstrap_config(subscription: DeviceProvisioning) -> State:
    """Apply bootstrap configuration to device"""
    
    # Apply configuration using Ansible
    deploy_result = execute_playbook(
        "ansible/operations/deploy_bootstrap_config.yaml",
        extra_vars={
            "device_ip": subscription.mgmt_ip,
            "device_platform": subscription.device_platform,
            "access_method": subscription.access_method,
            "configuration": subscription.generated_config,
            "backup_current": True,
            "commit_changes": True
        }
    )
    
    if not deploy_result.get("success"):
        raise RuntimeError(f"Failed to apply bootstrap configuration: {deploy_result.get('error')}")
    
    subscription.config_applied = True
    subscription.config_backup_id = deploy_result.get("backup_id")
    subscription.deployment_timestamp = deploy_result.get("timestamp")
    
    return subscription


@bootstrap_device_configuration.step("Verify Bootstrap Configuration")
def verify_bootstrap_config(subscription: DeviceProvisioning) -> State:
    """Verify bootstrap configuration was applied successfully"""
    
    # Verify configuration using Ansible
    verify_result = execute_playbook(
        "ansible/operations/verify_bootstrap_config.yaml",
        extra_vars={
            "device_ip": subscription.mgmt_ip,
            "device_platform": subscription.device_platform,
            "expected_config": subscription.generated_config,
            "verify_connectivity": True,
            "verify_services": ["ssh", "snmp", "ntp"]
        }
    )
    
    if not verify_result.get("success"):
        raise RuntimeError(f"Bootstrap configuration verification failed: {verify_result.get('error')}")
    
    verification_results = verify_result.get("verification_results", {})
    
    subscription.config_verified = True
    subscription.connectivity_verified = verification_results.get("connectivity", False)
    subscription.services_verified = verification_results.get("services", {})
    
    return subscription


@bootstrap_device_configuration.step("Setup Monitoring")
def setup_monitoring(subscription: DeviceProvisioning) -> State:
    """Setup initial device monitoring"""
    
    # Configure SNMP monitoring
    monitor_result = execute_playbook(
        "ansible/operations/setup_device_monitoring.yaml",
        extra_vars={
            "device_ip": subscription.mgmt_ip,
            "device_platform": subscription.device_platform,
            "snmp_community": subscription.snmp_community,
            "monitoring_profiles": ["basic_connectivity", "interface_status", "system_health"]
        }
    )
    
    if monitor_result.get("success"):
        subscription.monitoring_enabled = True
        subscription.monitoring_profiles = monitor_result.get("active_profiles", [])
    
    return subscription


@bootstrap_device_configuration.step("Register in NetBox")
def register_in_netbox(subscription: DeviceProvisioning) -> State:
    """Update device record in NetBox with bootstrap information"""
    
    # Update NetBox device record
    netbox_update = {
        "primary_ip4": subscription.mgmt_ip,
        "status": "active",
        "platform": subscription.device_platform,
        "comments": f"Bootstrap completed on {subscription.deployment_timestamp}",
        "custom_fields": {
            "bootstrap_template": subscription.config_template,
            "config_checksum": subscription.config_checksum,
            "monitoring_enabled": subscription.monitoring_enabled
        }
    }
    
    try:
        netbox.update_device(subscription.device_id, netbox_update)
        subscription.netbox_updated = True
    except Exception as e:
        # Log error but don't fail workflow
        subscription.netbox_error = str(e)
        subscription.netbox_updated = False
    
    return subscription


# NetBox Integration Helper Functions

def get_unbootstrapped_devices_from_netbox() -> List[tuple]:
    """Get devices that haven't been bootstrapped yet"""
    try:
        devices = netbox.get_devices(status="planned")  # Planned devices need bootstrapping
        bootstrap_devices = []
        
        for device in devices:
            # Only include devices that are ready for bootstrap
            if not device.get("custom_fields", {}).get("bootstrapped", False):
                site_name = device.get("site", {}).get("name", "Unknown")
                role_name = device.get("device_role", {}).get("name", "Unknown")
                display_name = f"{device['name']} ({role_name} - {site_name})"
                bootstrap_devices.append((str(device["id"]), display_name))
        
        return bootstrap_devices if bootstrap_devices else [("manual", "Manual Device Entry")]
    except:
        return [("manual", "Manual Device Entry")]


def get_templates_by_device_role_from_netbox() -> List[tuple]:
    """Get configuration templates based on device roles in NetBox"""
    try:
        device_roles = netbox.get_device_roles()
        template_options = []
        
        role_template_mapping = {
            "core-switch": ("core_switch", "Core Switch Template"),
            "distribution-switch": ("distribution_switch", "Distribution Switch Template"),
            "access-switch": ("access_switch", "Access Switch Template"),
            "router": ("router", "Router Template"),
            "firewall": ("firewall", "Firewall Template"),
            "wireless-controller": ("wireless_controller", "Wireless Controller Template"),
            "border-router": ("border_router", "Border Router Template"),
            "spine": ("spine_switch", "Spine Switch Template"),
            "leaf": ("leaf_switch", "Leaf Switch Template")
        }
        
        for role in device_roles:
            role_slug = role.get("slug", "")
            if role_slug in role_template_mapping:
                template_options.append(role_template_mapping[role_slug])
        
        # Always include custom option
        template_options.append(("custom", "Custom Template"))
        
        return template_options if template_options else [("custom", "Custom Template")]
    except:
        return [
            ("core_switch", "Core Switch Template"),
            ("distribution_switch", "Distribution Switch Template"),
            ("access_switch", "Access Switch Template"),
            ("router", "Router Template"),
            ("custom", "Custom Template")
        ]


def get_available_mgmt_ips_from_netbox() -> List[tuple]:
    """Get available management IPs from NetBox IPAM"""
    try:
        # Get management prefixes
        mgmt_prefixes = netbox.get_prefixes(role="management", status="active")
        available_ips = []
        
        for prefix in mgmt_prefixes:
            # Get available IPs in this prefix
            available = netbox.get_available_ips(prefix["id"], limit=10)
            for ip in available:
                site_name = prefix.get("site", {}).get("name", "Global")
                available_ips.append((ip, f"{ip} ({site_name})"))
        
        return available_ips if available_ips else [("manual", "Manual IP Entry")]
    except:
        return [("manual", "Manual IP Entry")]


def get_mgmt_subnet_mask_from_netbox() -> str:
    """Get management subnet mask from NetBox prefixes"""
    try:
        mgmt_prefixes = netbox.get_prefixes(role="management", status="active")
        if mgmt_prefixes:
            # Use first management prefix to determine subnet mask
            prefix_len = mgmt_prefixes[0]["prefix"].split("/")[1]
            # Convert CIDR to subnet mask
            cidr_to_mask = {
                "8": "255.0.0.0", "16": "255.255.0.0", "24": "255.255.255.0",
                "25": "255.255.255.128", "26": "255.255.255.192", 
                "27": "255.255.255.224", "28": "255.255.255.240"
            }
            return cidr_to_mask.get(prefix_len, "255.255.255.0")
    except:
        pass
    return "255.255.255.0"


def get_mgmt_gateway_from_netbox() -> str:
    """Get management gateway from NetBox prefixes"""
    try:
        mgmt_prefixes = netbox.get_prefixes(role="management", status="active")
        if mgmt_prefixes:
            # Assume gateway is first IP in prefix
            import ipaddress
            network = ipaddress.IPv4Network(mgmt_prefixes[0]["prefix"])
            return str(network.network_address + 1)
    except:
        pass
    return "192.168.1.1"


def get_site_primary_dns_from_netbox() -> str:
    """Get site primary DNS from NetBox configuration"""
    try:
        # Try to get DNS from site custom configuration
        dns_config = netbox.get_custom_config("dns_servers")
        if dns_config and "primary" in dns_config:
            return dns_config["primary"]
    except:
        pass
    return "8.8.8.8"


def get_site_secondary_dns_from_netbox() -> str:
    """Get site secondary DNS from NetBox configuration"""
    try:
        dns_config = netbox.get_custom_config("dns_servers")
        if dns_config and "secondary" in dns_config:
            return dns_config["secondary"]
    except:
        pass
    return "8.8.4.4"


def get_site_domain_from_netbox() -> str:
    """Get domain name from site configuration"""
    try:
        site_config = netbox.get_custom_config("site_domain")
        if site_config:
            return site_config
    except:
        pass
    return "local"


def get_site_ntp_server_from_netbox() -> str:
    """Get NTP server from site configuration"""
    try:
        ntp_config = netbox.get_custom_config("ntp_servers")
        if ntp_config and "primary" in ntp_config:
            return ntp_config["primary"]
    except:
        pass
    return "pool.ntp.org"


def get_timezone_choices() -> List[tuple]:
    """Get timezone choices"""
    return [
        ("UTC", "UTC"),
        ("America/New_York", "Eastern Time"),
        ("America/Chicago", "Central Time"),
        ("America/Denver", "Mountain Time"),
        ("America/Los_Angeles", "Pacific Time"),
        ("Europe/London", "GMT"),
        ("Europe/Amsterdam", "CET"),
        ("Asia/Tokyo", "JST"),
        ("Australia/Sydney", "AEST")
    ]


def get_site_timezone_from_netbox() -> str:
    """Get timezone from site location"""
    try:
        site_config = netbox.get_custom_config("timezone")
        if site_config:
            return site_config
    except:
        pass
    return "UTC"


def get_snmp_community_from_netbox() -> str:
    """Get SNMP community from NetBox secrets"""
    try:
        snmp_secret = netbox.get_secret("snmp_community")
        if snmp_secret:
            return snmp_secret
    except:
        pass
    return "public"


def get_snmp_location_from_netbox() -> str:
    """Get SNMP location from site information"""
    try:
        # This would use the site physical address
        site_info = netbox.get_custom_config("site_info")
        if site_info and "physical_address" in site_info:
            return site_info["physical_address"]
    except:
        pass
    return ""
