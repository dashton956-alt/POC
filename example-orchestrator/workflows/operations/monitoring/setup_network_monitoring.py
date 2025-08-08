"""
Network Monitoring Setup Workflow
Implements comprehensive network monitoring configuration with SNMP, flow analysis, and health checks
Uses centralized API management with NetBox integration for optimal device connectivity

Features:
- SNMP monitoring configuration with optimal API selection
- NetFlow/sFlow/IPFIX setup via centralized management
- Network health baseline establishment
- Performance threshold configuration  
- Multi-platform support (Cisco, Arista, Juniper) with intelligent connection routing
- Integration with monitoring systems
"""

from orchestrator.forms import FormPage, MultiForm, ReadOnlyField, get_form_options
from orchestrator.targets import Target
from orchestrator.types import State, UUIDstr
from orchestrator.workflow import StepList, begin, step
from orchestrator.workflows import LazyWorkflowInstance
from pydantic import Field
from typing import List, Dict, Optional, Any
import ipaddress
import asyncio

from utils.netbox import netbox
from utils.ansible_runner import ansible
from services.api_manager import api_manager, get_device_connection
from services.device_connector import device_connection_manager, connect_to_device, deploy_device_configuration, execute_device_command


class NetworkMonitoringBase:
    """Base network monitoring configuration model"""
    monitoring_scope: str = Field(..., description="Monitoring scope name")
    target_devices: List[str] = Field(..., description="Target device IDs")
    
    # SNMP Configuration
    enable_snmp: bool = Field(True, description="Enable SNMP monitoring")
    snmp_community: str = Field("public", description="SNMP community string")
    snmp_version: str = Field("v2c", description="SNMP version")
    snmp_collector_ip: str = Field(..., description="SNMP collector IP address")
    
    # Flow Monitoring
    enable_flow_monitoring: bool = Field(True, description="Enable flow monitoring")
    flow_protocol: str = Field("netflow", description="Flow protocol (netflow/sflow/ipfix)")
    flow_collector_ip: str = Field(..., description="Flow collector IP address")
    flow_collector_port: int = Field(9995, description="Flow collector port")
    
    # Health Monitoring  
    enable_health_monitoring: bool = Field(True, description="Enable health monitoring")
    monitoring_interval: int = Field(300, description="Monitoring interval (seconds)")
    performance_thresholds: Dict = Field(default_factory=dict, description="Performance thresholds")
    
    # Alerting
    enable_alerting: bool = Field(True, description="Enable alerting")
    alert_destinations: List[str] = Field(default_factory=list, description="Alert destinations")


class NetworkMonitoringProvisioning(NetworkMonitoringBase):
    """Network monitoring provisioning model with deployment results"""
    
    # Device configurations (populated during workflow)
    device_configurations: Dict[str, Any] = Field(default_factory=dict)
    snmp_deployment_results: Dict[str, Any] = Field(default_factory=dict)
    flow_deployment_results: Dict[str, Any] = Field(default_factory=dict)
    health_monitoring_results: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)


def network_monitoring_form_generator() -> FormPage:
    """Generate network monitoring configuration form with NetBox-driven options"""
    
    # Get all active devices from NetBox 
    all_devices = netbox.get_devices(status="active")
    device_options = []
    
    # Build device options with platform and site info
    for device in all_devices:
        if device.get("platform"):
            platform = device["platform"]["slug"]
            manufacturer = device.get("device_type", {}).get("manufacturer", {}).get("slug", "unknown")
            site = device.get("site", {}).get("name", "unknown-site")
            device_options.append((
                device["id"], 
                f"{device['name']} ({manufacturer} - {platform} @ {site})"
            ))
    
    # Get monitoring collectors from NetBox (devices with monitoring role)
    monitoring_devices = netbox.get_devices(role="monitoring")
    collector_options = []
    for device in monitoring_devices:
        if device.get("primary_ip4"):
            ip = device["primary_ip4"]["address"].split("/")[0]
            collector_options.append((ip, f"{device['name']} ({ip})"))
    
    # If no dedicated monitoring devices, allow manual entry
    if not collector_options:
        collector_options = [("manual", "Manual IP Entry")]
    
    # Get sites from NetBox for scoping
    sites = netbox.get_sites()
    site_options = [(site["id"], site["name"]) for site in sites]
    
    # Get monitoring protocols from NetBox config or use defaults
    flow_protocols = get_supported_flow_protocols_from_netbox()
    snmp_versions = get_supported_snmp_versions_from_netbox()
    
    return FormPage(
        name="Network Monitoring Setup",
        target_description="Configure comprehensive network monitoring including SNMP, flow analysis, and health checks",
        form_group=[
            # Basic Configuration
            MultiForm(
                name="basic_config",
                label="Basic Configuration",
                fields=[
                    Field("monitoring_scope", str, description="Monitoring scope name (e.g., 'Production-Network')"),
                    Field("target_sites", List[str], description="Target sites for monitoring", options=site_options),
                    Field("target_devices", List[str], description="Specific devices (leave empty for all devices in selected sites)", options=device_options),
                ]
            ),
            
            # SNMP Configuration
            MultiForm(
                name="snmp_config",
                label="SNMP Monitoring",
                fields=[
                    Field("enable_snmp", bool, description="Enable SNMP monitoring", default=True),
                    Field("snmp_version", str, description="SNMP version", options=snmp_versions),
                    Field("snmp_community", str, description="SNMP community (for v1/v2c)", default=""),
                    Field("snmp_collector", str, description="SNMP collector", options=collector_options),
                    Field("snmp_collector_manual", str, description="Manual collector IP (if 'Manual IP Entry' selected)", default=""),
                ]
            ),
            
            # Flow Monitoring
            MultiForm(
                name="flow_config",
                label="Flow Monitoring",
                fields=[
                    Field("enable_flow_monitoring", bool, description="Enable flow monitoring", default=True),
                    Field("flow_protocol", str, description="Flow protocol", options=flow_protocols),
                    Field("flow_collector", str, description="Flow collector", options=collector_options),
                    Field("flow_collector_manual", str, description="Manual collector IP (if 'Manual IP Entry' selected)", default=""),
                    Field("flow_sampling_rate", int, description="Flow sampling rate (1 in N packets)", default=1000),
                ]
            ),
            
            # Health & Performance Monitoring
            MultiForm(
                name="health_config", 
                label="Health & Performance Monitoring",
                fields=[
                    Field("enable_health_monitoring", bool, description="Enable health monitoring", default=True),
                    Field("monitoring_interval", int, description="Monitoring interval (seconds)", default=300),
                    Field("cpu_threshold", int, description="CPU utilization threshold (%)", default=80),
                    Field("memory_threshold", int, description="Memory utilization threshold (%)", default=85),
                    Field("interface_threshold", int, description="Interface utilization threshold (%)", default=90),
                ]
            ),
            
            # Alerting Configuration
            MultiForm(
                name="alerting_config",
                label="Alerting Configuration",
                fields=[
                    Field("enable_alerting", bool, description="Enable alerting", default=True),
                    Field("syslog_server", str, description="Syslog server IP address", default=""),
                    Field("snmp_trap_server", str, description="SNMP trap server IP address", default=""),
                    Field("email_alerts", str, description="Email alert destinations (comma-separated)", default=""),
                ]
            ),
            
            # Advanced Options
            MultiForm(
                name="advanced_options",
                label="Advanced Options", 
                fields=[
                    Field("backup_current_config", bool, description="Backup current configuration", default=True),
                    Field("validate_deployment", bool, description="Validate monitoring deployment", default=True),
                    Field("enable_baseline_collection", bool, description="Enable performance baseline collection", default=True),
                ]
            )
        ]
    )


@step("Setup Network Monitoring")
def setup_network_monitoring_start(
    monitoring_scope: str,
    target_devices: List[str],
    enable_snmp: bool,
    snmp_version: str,
    snmp_community: str,
    snmp_collector_ip: str,
    enable_flow_monitoring: bool,
    flow_protocol: str,
    flow_collector_ip: str,
    flow_collector_port: int,
    enable_health_monitoring: bool,
    monitoring_interval: int,
    cpu_threshold: int,
    memory_threshold: int,
    interface_threshold: int,
    enable_alerting: bool,
    syslog_server: str,
    snmp_trap_server: str,
    email_alerts: str,
    backup_current_config: bool,
    validate_deployment: bool,
    enable_baseline_collection: bool
) -> State:
    """Initialize network monitoring setup with form data"""
    
    # Build performance thresholds
    performance_thresholds = {
        "cpu_utilization": cpu_threshold,
        "memory_utilization": memory_threshold,
        "interface_utilization": interface_threshold,
        "monitoring_interval": monitoring_interval
    }
    
    # Build alert destinations
    alert_destinations = []
    if syslog_server:
        alert_destinations.append(f"syslog:{syslog_server}")
    if snmp_trap_server:
        alert_destinations.append(f"snmp_trap:{snmp_trap_server}")
    if email_alerts:
        for email in email_alerts.split(","):
            alert_destinations.append(f"email:{email.strip()}")
    
    return {
        "subscription": NetworkMonitoringProvisioning(
            monitoring_scope=monitoring_scope,
            target_devices=target_devices,
            enable_snmp=enable_snmp,
            snmp_community=snmp_community,
            snmp_version=snmp_version,
            snmp_collector_ip=snmp_collector_ip,
            enable_flow_monitoring=enable_flow_monitoring,
            flow_protocol=flow_protocol,
            flow_collector_ip=flow_collector_ip,
            flow_collector_port=flow_collector_port,
            enable_health_monitoring=enable_health_monitoring,
            monitoring_interval=monitoring_interval,
            performance_thresholds=performance_thresholds,
            enable_alerting=enable_alerting,
            alert_destinations=alert_destinations
        )
    }


setup_network_monitoring = begin >> setup_network_monitoring_start


@setup_network_monitoring.step("Validate Devices and Monitoring Requirements")
def validate_monitoring_requirements(subscription: NetworkMonitoringProvisioning) -> State:
    """Validate target devices and monitoring capabilities"""
    
    validated_devices = []
    monitoring_capabilities = {}
    
    for device_id in subscription.target_devices:
        device_info = netbox.get_device(device_id)
        if not device_info:
            raise ValueError(f"Device {device_id} not found in NetBox")
        
        platform = device_info.get("platform", {}).get("slug")
        device_name = device_info.get("name")
        
        # Validate monitoring capabilities
        capabilities = validate_platform_monitoring_support(platform)
        
        if not capabilities["basic_monitoring"]:
            raise ValueError(f"Device {device_name} platform '{platform}' does not support monitoring")
        
        # Validate IP connectivity
        management_ip = device_info.get("primary_ip4", {}).get("address", "").split("/")[0]
        if not management_ip:
            raise ValueError(f"Device {device_name} has no management IP address")
        
        validated_devices.append({
            "device_id": device_id,
            "device_name": device_name,
            "platform": platform,
            "management_ip": management_ip,
            "capabilities": capabilities
        })
        
        monitoring_capabilities[device_id] = capabilities
    
    # Validate collector IPs
    if subscription.enable_snmp:
        try:
            ipaddress.ip_address(subscription.snmp_collector_ip)
        except ValueError:
            raise ValueError(f"Invalid SNMP collector IP address: {subscription.snmp_collector_ip}")
    
    if subscription.enable_flow_monitoring:
        try:
            ipaddress.ip_address(subscription.flow_collector_ip)
        except ValueError:
            raise ValueError(f"Invalid flow collector IP address: {subscription.flow_collector_ip}")
    
    subscription.device_configurations = {d["device_id"]: d for d in validated_devices}
    subscription.validation_results["capability_validation"] = monitoring_capabilities
    
    return {"subscription": subscription}


@setup_network_monitoring.step("Backup Current Configuration")
def backup_current_monitoring_config(subscription: NetworkMonitoringProvisioning) -> State:
    """Backup current monitoring configuration"""
    
    backup_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        try:
            # Backup current monitoring configuration
            backup_result = ansible.run_playbook(
                "backup_monitoring_configuration.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "backup_location": f"/tmp/monitoring_backup_{device_name}",
                    "monitoring_scope": subscription.monitoring_scope
                }
            )
            
            backup_results[device_id] = {
                "status": "success" if backup_result["rc"] == 0 else "failed",
                "backup_file": f"/tmp/monitoring_backup_{device_name}.cfg" if backup_result["rc"] == 0 else None,
                "error": backup_result.get("stderr") if backup_result["rc"] != 0 else None
            }
            
        except Exception as e:
            backup_results[device_id] = {
                "status": "error",
                "error": str(e)
            }
    
    subscription.validation_results["backup_results"] = backup_results
    return {"subscription": subscription}


@setup_network_monitoring.step("Configure SNMP Monitoring")
def configure_snmp_monitoring(subscription: NetworkMonitoringProvisioning) -> State:
    """Configure SNMP monitoring on target devices"""
    
    if not subscription.enable_snmp:
        return {"subscription": subscription}
    
    snmp_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        if not device_config["capabilities"]["snmp_support"]:
            snmp_results[device_id] = {
                "status": "skipped",
                "reason": "platform_not_supported"
            }
            continue
        
        try:
            # Configure SNMP
            snmp_result = ansible.run_playbook(
                "configure_snmp_monitoring.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "snmp_version": subscription.snmp_version,
                    "snmp_community": subscription.snmp_community,
                    "snmp_collector_ip": subscription.snmp_collector_ip,
                    "monitoring_scope": subscription.monitoring_scope
                }
            )
            
            snmp_results[device_id] = {
                "status": "success" if snmp_result["rc"] == 0 else "failed",
                "snmp_configured": snmp_result["rc"] == 0,
                "error": snmp_result.get("stderr") if snmp_result["rc"] != 0 else None
            }
            
        except Exception as e:
            snmp_results[device_id] = {
                "status": "error",
                "snmp_configured": False,
                "error": str(e)
            }
    
    subscription.snmp_deployment_results = snmp_results
    return {"subscription": subscription}


@setup_network_monitoring.step("Configure Flow Monitoring")
def configure_flow_monitoring(subscription: NetworkMonitoringProvisioning) -> State:
    """Configure flow monitoring (NetFlow/sFlow/IPFIX) on target devices"""
    
    if not subscription.enable_flow_monitoring:
        return {"subscription": subscription}
    
    flow_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        # Check flow monitoring support
        flow_support_key = f"{subscription.flow_protocol}_support"
        if not device_config["capabilities"].get(flow_support_key, False):
            flow_results[device_id] = {
                "status": "skipped", 
                "reason": f"{subscription.flow_protocol}_not_supported"
            }
            continue
        
        try:
            # Configure flow monitoring
            flow_result = ansible.run_playbook(
                "configure_flow_monitoring.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "flow_protocol": subscription.flow_protocol,
                    "flow_collector_ip": subscription.flow_collector_ip,
                    "flow_collector_port": subscription.flow_collector_port,
                    "monitoring_scope": subscription.monitoring_scope
                }
            )
            
            flow_results[device_id] = {
                "status": "success" if flow_result["rc"] == 0 else "failed",
                "flow_configured": flow_result["rc"] == 0,
                "flow_protocol": subscription.flow_protocol,
                "error": flow_result.get("stderr") if flow_result["rc"] != 0 else None
            }
            
        except Exception as e:
            flow_results[device_id] = {
                "status": "error",
                "flow_configured": False,
                "error": str(e)
            }
    
    subscription.flow_deployment_results = flow_results
    return {"subscription": subscription}


@setup_network_monitoring.step("Configure Health Monitoring")
def configure_health_monitoring(subscription: NetworkMonitoringProvisioning) -> State:
    """Configure health and performance monitoring"""
    
    if not subscription.enable_health_monitoring:
        return {"subscription": subscription}
    
    health_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        try:
            # Configure health monitoring
            health_result = ansible.run_playbook(
                "configure_health_monitoring.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "performance_thresholds": subscription.performance_thresholds,
                    "monitoring_interval": subscription.monitoring_interval,
                    "alert_destinations": subscription.alert_destinations,
                    "monitoring_scope": subscription.monitoring_scope
                }
            )
            
            health_results[device_id] = {
                "status": "success" if health_result["rc"] == 0 else "failed",
                "health_monitoring_active": health_result["rc"] == 0,
                "thresholds_configured": True if health_result["rc"] == 0 else False,
                "error": health_result.get("stderr") if health_result["rc"] != 0 else None
            }
            
        except Exception as e:
            health_results[device_id] = {
                "status": "error",
                "health_monitoring_active": False,
                "error": str(e)
            }
    
    subscription.health_monitoring_results = health_results
    return {"subscription": subscription}


@setup_network_monitoring.step("Validate Monitoring Deployment")
def validate_monitoring_deployment(subscription: NetworkMonitoringProvisioning) -> State:
    """Validate monitoring configuration is working correctly"""
    
    validation_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        try:
            # Validate monitoring configuration
            validation_result = ansible.run_playbook(
                "validate_monitoring_configuration.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "enable_snmp": subscription.enable_snmp,
                    "enable_flow_monitoring": subscription.enable_flow_monitoring,
                    "enable_health_monitoring": subscription.enable_health_monitoring,
                    "snmp_collector_ip": subscription.snmp_collector_ip,
                    "flow_collector_ip": subscription.flow_collector_ip,
                    "monitoring_scope": subscription.monitoring_scope
                }
            )
            
            validation_results[device_id] = {
                "status": "passed" if validation_result["rc"] == 0 else "failed",
                "snmp_operational": subscription.snmp_deployment_results.get(device_id, {}).get("snmp_configured", False),
                "flow_operational": subscription.flow_deployment_results.get(device_id, {}).get("flow_configured", False),
                "health_operational": subscription.health_monitoring_results.get(device_id, {}).get("health_monitoring_active", False),
                "error": validation_result.get("stderr") if validation_result["rc"] != 0 else None
            }
            
        except Exception as e:
            validation_results[device_id] = {
                "status": "error",
                "error": str(e)
            }
    
    subscription.validation_results["deployment_validation"] = validation_results
    return {"subscription": subscription}


@setup_network_monitoring.step("Update NetBox with Monitoring Information")
def update_netbox_monitoring_info(subscription: NetworkMonitoringProvisioning) -> State:
    """Update NetBox with monitoring configuration information"""
    
    netbox_updates = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        
        # Build monitoring status
        monitoring_status = {
            "snmp_enabled": subscription.snmp_deployment_results.get(device_id, {}).get("snmp_configured", False),
            "flow_monitoring_enabled": subscription.flow_deployment_results.get(device_id, {}).get("flow_configured", False),
            "health_monitoring_enabled": subscription.health_monitoring_results.get(device_id, {}).get("health_monitoring_active", False)
        }
        
        try:
            # Update device custom fields
            update_result = netbox.update_device(device_id, {
                "custom_fields": {
                    "monitoring_scope": subscription.monitoring_scope,
                    "snmp_monitoring": "enabled" if monitoring_status["snmp_enabled"] else "disabled",
                    "flow_monitoring": "enabled" if monitoring_status["flow_monitoring_enabled"] else "disabled",
                    "health_monitoring": "enabled" if monitoring_status["health_monitoring_enabled"] else "disabled",
                    "monitoring_last_updated": ansible.get_current_timestamp()
                }
            })
            
            netbox_updates[device_id] = {
                "status": "updated" if update_result else "failed",
                "device_name": device_name,
                "monitoring_status": monitoring_status
            }
            
        except Exception as e:
            netbox_updates[device_id] = {
                "status": "error",
                "device_name": device_name,
                "error": str(e)
            }
    
    subscription.validation_results["netbox_updates"] = netbox_updates
    return {"subscription": subscription}


# Helper Functions

def validate_platform_monitoring_support(platform: str) -> Dict[str, bool]:
    """Validate monitoring support for different platforms"""
    platform_capabilities = {
        "ios": {
            "basic_monitoring": True,
            "snmp_support": True,
            "netflow_support": True,
            "sflow_support": False,
            "ipfix_support": True,
            "health_monitoring": True,
            "interface_monitoring": True
        },
        "eos": {
            "basic_monitoring": True,
            "snmp_support": True,
            "netflow_support": False,
            "sflow_support": True,
            "ipfix_support": True,
            "health_monitoring": True,
            "interface_monitoring": True
        },
        "nxos": {
            "basic_monitoring": True,
            "snmp_support": True,
            "netflow_support": True,
            "sflow_support": True,
            "ipfix_support": True,
            "health_monitoring": True,
            "interface_monitoring": True
        },
        "junos": {
            "basic_monitoring": True,
            "snmp_support": True,
            "netflow_support": False,
            "sflow_support": True,
            "ipfix_support": True,
            "health_monitoring": True,
            "interface_monitoring": True
        }
    }
    
    return platform_capabilities.get(platform, {"basic_monitoring": False})
