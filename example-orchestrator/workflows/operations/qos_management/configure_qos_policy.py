"""
Configure QoS Policy Workflow
Implement Quality of Service policies with traffic prioritization and bandwidth management
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

from products.product_types.qos import QoSInactive, QoSProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from services.api_manager import api_manager, get_device_connection
from services.device_connector import device_connection_manager, connect_to_device, deploy_device_configuration, execute_device_command
from workflows.shared import device_selector

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


class QoSPolicyBase:
    """Base QoS Policy configuration model"""
    policy_name: str = Field(..., description="QoS policy name")
    description: Optional[str] = Field(None, description="Policy description")
    target_devices: List[str] = Field(..., description="Target device IDs")
    
    # Traffic Classification
    classification_rules: List[Dict] = Field(default_factory=list, description="Traffic classification rules")
    
    # Queue Configuration  
    queue_config: Dict = Field(default_factory=dict, description="Queue configuration")
    
    # Bandwidth Management
    bandwidth_policies: List[Dict] = Field(default_factory=list, description="Bandwidth allocation policies")
    
    # Validation settings
    validate_deployment: bool = Field(True, description="Validate policy deployment")
    backup_current_config: bool = Field(True, description="Backup current configuration")


class QoSPolicyProvisioning(QoSPolicyBase):
    """QoS policy provisioning model with extended configuration"""
    
    # Device-specific configurations (populated during workflow)
    device_configurations: Dict[str, Any] = Field(default_factory=dict)
    configuration_backups: Dict[str, str] = Field(default_factory=dict)
    deployment_results: Dict[str, Any] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)


def qos_policy_form_generator() -> FormPage:
    """Generate QoS policy configuration form with NetBox-driven options"""
    
    # Get all active devices from NetBox
    all_devices = netbox.get_devices(status="active")
    device_options = []
    
    # Build device options with platform and manufacturer info
    for device in all_devices:
        if device.get("platform"):
            platform = device["platform"]["slug"]
            manufacturer = device.get("device_type", {}).get("manufacturer", {}).get("slug", "unknown")
            device_options.append((
                device["id"], 
                f"{device['name']} ({manufacturer} - {platform})"
            ))
    
    # Get available platforms from NetBox for validation
    platforms = netbox.get_platforms()
    supported_platforms = [p for p in platforms if p["slug"] in ["ios", "eos", "nxos", "junos", "iosxr"]]
    
    # Get QoS classes from NetBox custom fields or use defaults
    qos_classes = get_qos_classes_from_netbox() or [
        ("voice", "Voice Traffic"),
        ("video", "Video Traffic"), 
        ("critical_data", "Critical Data"),
        ("business_data", "Business Data"),
        ("best_effort", "Best Effort")
    ]
    
    return FormPage(
        name="QoS Policy Configuration",
        target_description="Configure Quality of Service policies for traffic prioritization and bandwidth management",
        form_group=[
            # Policy Basic Information
            MultiForm(
                name="policy_info",
                label="Policy Information",
                fields=[
                    Field("policy_name", str, description="QoS policy name (e.g., 'WAN-QoS-Policy')"),
                    Field("description", Optional[str], description="Policy description"),
                    Field("target_devices", List[str], description="Target devices", options=device_options),
                ]
            ),
            
            # Traffic Classification
            MultiForm(
                name="classification",
                label="Traffic Classification",
                fields=[
                    Field("classification_method", str, description="Classification method", 
                          options=[("dscp", "DSCP Marking"), ("cos", "CoS Marking"), ("acl", "ACL-based"), ("nbar", "Application Recognition")]),
                    Field("enable_auto_qos", bool, description="Enable platform auto-QoS templates", default=False),
                    Field("voice_dscp", str, description="Voice traffic DSCP value", default="ef"),
                    Field("video_dscp", str, description="Video traffic DSCP value", default="af41"),
                    Field("data_dscp", str, description="Critical data DSCP value", default="af31")
                ]
            ),
            
            # Queue Configuration
            MultiForm(
                name="queuing",
                label="Queue Configuration",  
                fields=[
                    Field("queue_strategy", str, description="Queuing strategy", 
                          options=[("platform_default", "Platform Default"), ("custom", "Custom Configuration")]),
                    Field("priority_queue_percent", int, description="Priority queue percentage (1-50)", default=30),
                    Field("voice_bandwidth_percent", int, description="Voice bandwidth percentage", default=30),
                    Field("video_bandwidth_percent", int, description="Video bandwidth percentage", default=25),
                    Field("data_bandwidth_percent", int, description="Data bandwidth percentage", default=45)
                ]
            ),
            
            # Bandwidth Policies
            MultiForm(
                name="bandwidth",
                label="Bandwidth Management",
                fields=[
                    Field("interface_types", List[str], description="Interface types to apply QoS", 
                          options=get_interface_types_from_netbox()),
                    Field("wan_bandwidth_mbps", int, description="WAN bandwidth (Mbps) - leave 0 for auto-detect", default=0),
                    Field("enable_shaping", bool, description="Enable traffic shaping", default=True),
                    Field("shaping_strategy", str, description="Shaping strategy", 
                          options=[("percentage", "Percentage-based"), ("absolute", "Absolute values"), ("adaptive", "Adaptive")])
                ]
            ),
            
            # Advanced Settings
            MultiForm(
                name="advanced",
                label="Advanced Settings",
                fields=[
                    Field("validate_deployment", bool, description="Validate deployment", default=True),
                    Field("backup_current_config", bool, description="Backup current configuration", default=True),
                    Field("enable_monitoring", bool, description="Enable QoS monitoring", default=True),
                    Field("rollback_on_failure", bool, description="Auto-rollback on failure", default=True)
                ]
            )
        ]
    )


@step("Configure QoS Policy")
def configure_qos_policy_start(
    policy_name: str,
    description: Optional[str],
    target_devices: List[str],
    classification_method: str,
    enable_auto_qos: bool,
    voice_dscp: str,
    video_dscp: str,
    data_dscp: str,
    queue_strategy: str,
    priority_queue_percent: int,
    voice_bandwidth_percent: int,
    video_bandwidth_percent: int,
    data_bandwidth_percent: int,
    interface_types: List[str],
    wan_bandwidth_mbps: int,
    enable_shaping: bool,
    shaping_strategy: str,
    validate_deployment: bool,
    backup_current_config: bool,
    enable_monitoring: bool,
    rollback_on_failure: bool
) -> State:
    """Initialize QoS policy configuration with NetBox-driven form data"""
    
    # Build classification rules based on selected method
    classification_rules = []
    if classification_method == "dscp":
        classification_rules.append({
            "type": "dscp",
            "voice": voice_dscp,
            "video": video_dscp,
            "critical_data": data_dscp,
            "business_data": "af21",
            "best_effort": "default"
        })
    elif classification_method == "acl":
        classification_rules.append({
            "type": "acl_based",
            "use_auto_qos": enable_auto_qos
        })
    
    # Build queue configuration based on strategy
    queue_config = {
        "strategy": queue_strategy,
        "priority_percent": priority_queue_percent,
        "voice_percent": voice_bandwidth_percent,
        "video_percent": video_bandwidth_percent,
        "data_percent": data_bandwidth_percent,
        "interface_types": interface_types
    }
    
    # Build bandwidth policies with NetBox-driven interface detection
    bandwidth_policies = []
    if enable_shaping:
        # Auto-detect bandwidth if not specified
        if wan_bandwidth_mbps == 0:
            wan_bandwidth_mbps = auto_detect_interface_bandwidth(target_devices, interface_types)
        
        bandwidth_policies.append({
            "type": "interface_shaping",
            "bandwidth_mbps": wan_bandwidth_mbps,
            "strategy": shaping_strategy,
            "interface_types": interface_types
        })
    
    return {
        "subscription": QoSPolicyProvisioning(
            policy_name=policy_name,
            description=description,
            target_devices=target_devices,
            classification_rules=classification_rules,
            queue_config=queue_config,
            bandwidth_policies=bandwidth_policies,
            validate_deployment=validate_deployment,
            backup_current_config=backup_current_config
        )
    }


configure_qos_policy = begin >> configure_qos_policy_start


@configure_qos_policy.step("Validate Devices and Capabilities")
def validate_qos_capabilities(subscription: QoSPolicyProvisioning) -> State:
    """Validate target devices support QoS features"""
    
    validated_devices = []
    capability_matrix = {}
    
    for device_id in subscription.target_devices:
        device_info = netbox.get_device(device_id)
        if not device_info:
            raise ValueError(f"Device {device_id} not found in NetBox")
        
        platform = device_info.get("platform", {}).get("slug")
        device_name = device_info.get("name")
        
        # Platform-specific QoS capability validation
        capabilities = validate_platform_qos_support(platform)
        
        if not capabilities["basic_qos"]:
            raise ValueError(f"Device {device_name} platform '{platform}' does not support QoS")
        
        validated_devices.append({
            "device_id": device_id,
            "device_name": device_name,
            "platform": platform,
            "capabilities": capabilities,
            "management_ip": device_info.get("primary_ip4", {}).get("address", "").split("/")[0]
        })
        
        capability_matrix[device_id] = capabilities
    
    subscription.device_configurations = {d["device_id"]: d for d in validated_devices}
    subscription.deployment_results["capability_validation"] = capability_matrix
    
    return {"subscription": subscription}


@configure_qos_policy.step("Backup Current Configuration")  
def backup_current_qos_config(subscription: QoSPolicyProvisioning) -> State:
    """Backup current QoS configuration"""
    
    if not subscription.backup_current_config:
        return {"subscription": subscription}
    
    backup_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        
        try:
            # Run platform-specific backup playbook
            backup_result = ansible.run_playbook(
                "backup_qos_configuration.yaml",
                extra_vars={
                    "target_host": device_config["management_ip"],
                    "device_name": device_name,
                    "platform": platform,
                    "backup_location": f"/tmp/qos_backup_{device_name}_{subscription.policy_name}"
                }
            )
            
            if backup_result["rc"] == 0:
                backup_results[device_id] = {
                    "status": "success",
                    "backup_file": f"/tmp/qos_backup_{device_name}_{subscription.policy_name}.cfg",
                    "timestamp": backup_result["end"]
                }
            else:
                backup_results[device_id] = {
                    "status": "failed", 
                    "error": backup_result["stderr"]
                }
                
        except Exception as e:
            backup_results[device_id] = {
                "status": "error",
                "error": str(e)
            }
    
    subscription.configuration_backups = backup_results
    return {"subscription": subscription}


@configure_qos_policy.step("Generate QoS Configurations")
def generate_qos_configurations(subscription: QoSPolicyProvisioning) -> State:
    """Generate platform-specific QoS configurations"""
    
    configurations = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        platform = device_config["platform"]
        device_name = device_config["device_name"]
        
        # Generate platform-specific configuration
        config = generate_platform_qos_config(
            platform=platform,
            policy_name=subscription.policy_name,
            classification_rules=subscription.classification_rules,
            queue_config=subscription.queue_config,
            bandwidth_policies=subscription.bandwidth_policies
        )
        
        configurations[device_id] = {
            "device_name": device_name,
            "platform": platform,
            "configuration": config,
            "config_lines": len(config.split('\n')) if config else 0
        }
    
    subscription.deployment_results["generated_configs"] = configurations
    return {"subscription": subscription}


@configure_qos_policy.step("Deploy QoS Configuration via Optimal API")
async def deploy_qos_configuration(subscription: QoSPolicyProvisioning) -> State:
    """Deploy QoS configuration using optimal connection method (centralized API or direct)"""
    
    deployment_results = []
    
    for device_id, device_config in subscription.device_configurations.items():
        try:
            # Get optimal connection information
            connection_info = get_device_connection(device_id)
            
            # Log connection method being used
            connection_method = "Centralized API" if connection_info["use_centralized_api"] else "Direct SSH"
            api_endpoint = connection_info.get("api_endpoint", "N/A")
            device_ip = connection_info.get("device_ip", "Unknown")
            
            print(f"Deploying QoS to {device_id} ({device_ip}) via {connection_method}")
            if connection_info["use_centralized_api"]:
                print(f"  Using API endpoint: {api_endpoint}")
            
            # Get generated configuration for this device
            generated_config = subscription.deployment_results["generated_configs"][device_id]
            
            # Deploy configuration using optimal method
            deployment_result = await deploy_device_configuration(
                device_id,
                generated_config,
                template_name=f"QoS-{subscription.policy_name}",
                backup_before_change=subscription.backup_current_config
            )
            
            # Store deployment results
            deployment_results.append({
                "device_id": device_id,
                "device_name": device_config["device_name"],
                "device_ip": device_ip,
                "connection_method": connection_method,
                "api_endpoint": api_endpoint,
                "success": deployment_result.success,
                "deployment_method": deployment_result.method,
                "message": deployment_result.message,
                "config_lines": len(generated_config.split('\n')) if generated_config else 0
            })
            
            if not deployment_result.success:
                print(f"QoS deployment failed for {device_id}: {deployment_result.message}")
            else:
                print(f"QoS deployed successfully to {device_id} via {deployment_result.method}")
                
        except Exception as e:
            deployment_results.append({
                "device_id": device_id,
                "device_name": device_config.get("device_name", f"Device-{device_id}"),
                "success": False,
                "error": str(e),
                "connection_method": "Error",
                "api_endpoint": "N/A"
            })
            print(f"Error deploying QoS to {device_id}: {e}")
    
    # Store results in subscription
    subscription.deployment_results["api_deployments"] = deployment_results
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
    
    return subscription
                    "qos_configuration": generated_config["configuration"],
                    "validate_config": subscription.validate_deployment
                }
            )
            
            if deploy_result["rc"] == 0:
                deployment_results[device_id] = {
                    "status": "success",
                    "config_applied": True,
                    "lines_configured": generated_config["config_lines"],
                    "deployment_time": deploy_result["end"]
                }
            else:
                deployment_results[device_id] = {
                    "status": "failed",
                    "config_applied": False,
                    "error": deploy_result["stderr"]
                }
                
        except Exception as e:
            deployment_results[device_id] = {
                "status": "error",
                "config_applied": False,
                "error": str(e)
            }
    
    subscription.deployment_results["deployment"] = deployment_results
    return {"subscription": subscription}


@configure_qos_policy.step("Validate QoS Policy Deployment")
def validate_qos_deployment(subscription: QoSPolicyProvisioning) -> State:
    """Validate QoS policy is working correctly"""
    
    if not subscription.validate_deployment:
        return {"subscription": subscription}
    
    validation_results = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        platform = device_config["platform"]
        management_ip = device_config["management_ip"]
        
        try:
            # Run QoS validation playbook
            validation_result = ansible.run_playbook(
                "validate_qos_policy.yaml",
                extra_vars={
                    "target_host": management_ip,
                    "device_name": device_name,
                    "platform": platform,
                    "policy_name": subscription.policy_name,
                    "expected_queues": len(subscription.queue_config),
                    "expected_classes": len(subscription.classification_rules)
                }
            )
            
            if validation_result["rc"] == 0:
                validation_results[device_id] = {
                    "status": "passed",
                    "policy_active": True,
                    "queue_status": "operational",
                    "classification_active": True
                }
            else:
                validation_results[device_id] = {
                    "status": "failed",
                    "policy_active": False,
                    "error": validation_result["stderr"]
                }
                
        except Exception as e:
            validation_results[device_id] = {
                "status": "error",
                "policy_active": False,
                "error": str(e)
            }
    
    subscription.validation_results = validation_results
    return {"subscription": subscription}


@configure_qos_policy.step("Update NetBox with QoS Information")
def update_netbox_qos_info(subscription: QoSPolicyProvisioning) -> State:
    """Update NetBox with QoS policy information"""
    
    netbox_updates = {}
    
    for device_id, device_config in subscription.device_configurations.items():
        device_name = device_config["device_name"]
        deployment_status = subscription.deployment_results["deployment"][device_id]
        
        if deployment_status["status"] == "success":
            # Update device custom fields with QoS information
            update_result = netbox.update_device(device_id, {
                "custom_fields": {
                    "qos_policy": subscription.policy_name,
                    "qos_policy_status": "active",
                    "qos_last_updated": deployment_status["deployment_time"]
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
    
    subscription.deployment_results["netbox_updates"] = netbox_updates
    return {"subscription": subscription}


# Helper Functions

def validate_platform_qos_support(platform: str) -> Dict[str, bool]:
    """Validate QoS support for different platforms"""
    platform_capabilities = {
        "ios": {
            "basic_qos": True,
            "cbwfq": True,
            "priority_queue": True,
            "nbar": True,
            "traffic_shaping": True,
            "policing": True
        },
        "eos": {
            "basic_qos": True,
            "cbwfq": True,
            "priority_queue": True,
            "nbar": False,
            "traffic_shaping": True,
            "policing": True
        },
        "nxos": {
            "basic_qos": True,
            "cbwfq": True,
            "priority_queue": True,
            "nbar": False,
            "traffic_shaping": True,
            "policing": True
        },
        "junos": {
            "basic_qos": True,
            "cbwfq": True,
            "priority_queue": True,
            "nbar": False,
            "traffic_shaping": True,
            "policing": True
        }
    }
    
    return platform_capabilities.get(platform, {"basic_qos": False})


def generate_platform_qos_config(platform: str, policy_name: str, classification_rules: List[Dict], 
                                 queue_config: Dict, bandwidth_policies: List[Dict]) -> str:
    """Generate platform-specific QoS configuration"""
    
    if platform == "ios":
        return generate_ios_qos_config(policy_name, classification_rules, queue_config, bandwidth_policies)
    elif platform == "eos":
        return generate_eos_qos_config(policy_name, classification_rules, queue_config, bandwidth_policies)
    elif platform == "nxos":
        return generate_nxos_qos_config(policy_name, classification_rules, queue_config, bandwidth_policies)
    elif platform == "junos":
        return generate_junos_qos_config(policy_name, classification_rules, queue_config, bandwidth_policies)
    else:
        raise ValueError(f"Unsupported platform for QoS configuration: {platform}")


def generate_ios_qos_config(policy_name: str, classification_rules: List[Dict], 
                           queue_config: Dict, bandwidth_policies: List[Dict]) -> str:
    """Generate Cisco IOS QoS configuration"""
    
    config_lines = []
    
    # Class maps for traffic classification
    config_lines.extend([
        f"class-map match-all {policy_name}-VOICE",
        " match ip dscp ef",
        "!",
        f"class-map match-all {policy_name}-VIDEO", 
        " match ip dscp af41",
        "!",
        f"class-map match-all {policy_name}-CRITICAL-DATA",
        " match ip dscp af31",
        "!",
        f"class-map match-all {policy_name}-BUSINESS-DATA",
        " match ip dscp af21",
        "!"
    ])
    
    # Policy map for queuing
    config_lines.extend([
        f"policy-map {policy_name}",
        f" class {policy_name}-VOICE",
        f"  priority percent {queue_config.get('voice_percent', 30)}",
        f" class {policy_name}-VIDEO",
        f"  bandwidth percent {queue_config.get('video_percent', 25)}",
        f" class {policy_name}-CRITICAL-DATA",
        f"  bandwidth percent 20",
        f" class {policy_name}-BUSINESS-DATA", 
        f"  bandwidth percent 15",
        " class class-default",
        "  bandwidth percent 10",
        "  fair-queue",
        "!"
    ])
    
    # Interface shaping if enabled
    for bandwidth_policy in bandwidth_policies:
        if bandwidth_policy["type"] == "interface_shaping":
            config_lines.extend([
                f"policy-map {policy_name}-SHAPE",
                f" class class-default",
                f"  shape average {bandwidth_policy['bandwidth_mbps']}000000",
                f"  service-policy {policy_name}",
                "!"
            ])
    
    return "\n".join(config_lines)


def generate_eos_qos_config(policy_name: str, classification_rules: List[Dict],
                           queue_config: Dict, bandwidth_policies: List[Dict]) -> str:
    """Generate Arista EOS QoS configuration"""
    
    config_lines = []
    
    # Class maps
    config_lines.extend([
        f"class-map type qos match-all {policy_name}-VOICE",
        "   match ip access-group name VOICE-ACL",
        "!",
        f"class-map type qos match-all {policy_name}-VIDEO",
        "   match ip access-group name VIDEO-ACL", 
        "!",
        f"policy-map type qos {policy_name}",
        f"   class {policy_name}-VOICE",
        f"      set dscp ef",
        f"      police rate {queue_config.get('voice_percent', 30)} percent",
        f"   class {policy_name}-VIDEO",
        f"      set dscp af41",
        f"      police rate {queue_config.get('video_percent', 25)} percent",
        "!"
    ])
    
    return "\n".join(config_lines)


def generate_nxos_qos_config(policy_name: str, classification_rules: List[Dict],
                            queue_config: Dict, bandwidth_policies: List[Dict]) -> str:
    """Generate Cisco NX-OS QoS configuration"""
    
    config_lines = []
    
    # Type QoS class maps and policy maps
    config_lines.extend([
        f"class-map type qos match-all {policy_name}-VOICE",
        "  match dscp ef",
        "!",
        f"class-map type qos match-all {policy_name}-VIDEO",
        "  match dscp af41", 
        "!",
        f"policy-map type qos {policy_name}",
        f"  class {policy_name}-VOICE",
        f"    set qos-group 1",
        f"  class {policy_name}-VIDEO",
        f"    set qos-group 2",
        "!",
        f"class-map type queuing {policy_name}-VOICE-Q",
        "  match qos-group 1",
        "!",
        f"policy-map type queuing {policy_name}-OUT",
        f"  class type queuing {policy_name}-VOICE-Q",
        f"    priority level 1",
        f"    bandwidth percent {queue_config.get('voice_percent', 30)}",
        "!"
    ])
    
    return "\n".join(config_lines)


def generate_junos_qos_config(policy_name: str, classification_rules: List[Dict],
                             queue_config: Dict, bandwidth_policies: List[Dict]) -> str:
    """Generate Juniper JunOS QoS configuration"""
    
    config_lines = []
    
    # Juniper style configuration
    config_lines.extend([
        f"class-of-service {{",
        f"    classifiers {{",
        f"        dscp {policy_name}-classifier {{",
        f"            forwarding-class voice {{",
        f"                loss-priority low code-points ef;",
        f"            }}",
        f"            forwarding-class video {{", 
        f"                loss-priority low code-points af41;",
        f"            }}",
        f"        }}",
        f"    }}",
        f"    forwarding-classes {{",
        f"        queue 0 voice;",
        f"        queue 1 video;",
        f"        queue 2 data;",
        f"        queue 3 default;",
        f"    }}",
        f"    schedulers {{",
        f"        {policy_name}-scheduler {{",
        f"            transmit-rate percent {queue_config.get('voice_percent', 30)};",
        f"            buffer-size percent 30;",
        f"            priority high;",
        f"        }}",
        f"    }}",
        f"}}"
    ])
    
    return "\n".join(config_lines)


# NetBox Integration Helper Functions

def get_qos_classes_from_netbox() -> List[tuple]:
    """Get QoS classes from NetBox custom fields or configuration"""
    try:
        # Try to get QoS classes from NetBox custom fields
        custom_fields = netbox.get_custom_fields("qos_class")
        if custom_fields:
            return [(cf["value"], cf["label"]) for cf in custom_fields]
    except:
        pass
    
    # Return default classes if NetBox doesn't have custom ones
    return [
        ("voice", "Voice Traffic"),
        ("video", "Video Traffic"), 
        ("critical_data", "Critical Data"),
        ("business_data", "Business Data"),
        ("best_effort", "Best Effort")
    ]


def get_interface_types_from_netbox() -> List[tuple]:
    """Get interface types from NetBox for QoS application"""
    try:
        interface_types = netbox.get_interface_types()
        qos_applicable_types = []
        
        for itype in interface_types:
            # Filter for interface types where QoS is commonly applied
            if any(keyword in itype["slug"].lower() for keyword in ["ethernet", "gigabit", "10gig", "wan", "serial"]):
                qos_applicable_types.append((itype["slug"], itype["display"]))
        
        return qos_applicable_types
    except:
        # Fallback to common interface types
        return [
            ("1000base-t", "Gigabit Ethernet"),
            ("10gbase-x-sfpp", "10 Gigabit SFP+"),
            ("wan", "WAN Interface"),
            ("ethernet", "Generic Ethernet")
        ]


def auto_detect_interface_bandwidth(device_ids: List[str], interface_types: List[str]) -> int:
    """Auto-detect interface bandwidth from NetBox device interfaces"""
    total_bandwidth = 0
    interface_count = 0
    
    for device_id in device_ids:
        try:
            device_interfaces = netbox.get_device_interfaces(device_id)
            for interface in device_interfaces:
                if interface.get("type", {}).get("value") in interface_types:
                    # Extract bandwidth from interface type or custom fields
                    interface_bandwidth = extract_bandwidth_from_interface(interface)
                    if interface_bandwidth > 0:
                        total_bandwidth += interface_bandwidth
                        interface_count += 1
        except:
            continue
    
    # Return average bandwidth or default to 100 Mbps
    return int(total_bandwidth / interface_count) if interface_count > 0 else 100


def extract_bandwidth_from_interface(interface: Dict) -> int:
    """Extract bandwidth value from NetBox interface"""
    interface_type = interface.get("type", {}).get("value", "")
    
    # Common bandwidth mappings
    bandwidth_map = {
        "100base-tx": 100,
        "1000base-t": 1000,  
        "10gbase-x-sfpp": 10000,
        "25gbase-x-sfp28": 25000,
        "40gbase-x-qsfpp": 40000,
        "100gbase-x-qsfp28": 100000
    }
    
    # Check for exact match
    if interface_type in bandwidth_map:
        return bandwidth_map[interface_type]
    
    # Check for partial matches
    for itype, bandwidth in bandwidth_map.items():
        if itype in interface_type.lower():
            return bandwidth
    
    # Check custom fields for bandwidth
    custom_fields = interface.get("custom_fields", {})
    if "bandwidth" in custom_fields and custom_fields["bandwidth"]:
        try:
            return int(custom_fields["bandwidth"])
        except:
            pass
    
    return 0


def get_platform_qos_capabilities_from_netbox(platform_slug: str) -> Dict[str, bool]:
    """Get QoS capabilities for a platform from NetBox"""
    try:
        platform = netbox.get_platform(platform_slug)
        custom_fields = platform.get("custom_fields", {})
        
        # Check if NetBox has QoS capability information
        if "qos_capabilities" in custom_fields:
            return custom_fields["qos_capabilities"]
    except:
        pass
    
    # Fall back to hardcoded capabilities
    return validate_platform_qos_support(platform_slug)
