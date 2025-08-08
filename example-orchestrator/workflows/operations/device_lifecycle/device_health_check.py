"""
Device Health Check Workflow
Comprehensive device validation and health assessment
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
from typing import List, Dict, Any

from products.product_types.device import DeviceInactive, DeviceProvisioning
from services.netbox import netbox
from services.lso_client import execute_playbook
from services.api_manager import api_manager
from services.device_connector import device_connector
from workflows.shared import device_selector


class HealthCheckForm(FormPage):
    """Device health check configuration"""
    device_selection: Choice = Field(
        description="Device Selection Method",
        choices=[
            ("single_device", "Single Device"),
            ("device_group", "Device Group"),
            ("site_devices", "All Devices in Site"),
            ("device_type", "Devices by Type"),
            ("all_devices", "All Network Devices")
        ]
    )
    device_id: str = Field(
        description="Device ID (if single device)",
        required=False
    )
    site_name: str = Field(
        description="Site Name (if site selection)",
        required=False
    )
    device_type_filter: str = Field(
        description="Device Type Filter",
        required=False
    )
    check_types: List[Choice] = Field(
        description="Health Check Types",
        choices=[
            ("hardware", "Hardware Status"),
            ("software", "Software Version"),
            ("interfaces", "Interface Status"),
            ("protocols", "Protocol Status"),
            ("performance", "Performance Metrics"),
            ("security", "Security Compliance"),
            ("configuration", "Configuration Compliance")
        ],
        default=["hardware", "software", "interfaces"]
    )
    generate_report: bool = Field(
        description="Generate Health Report",
        default=True
    )
    remediation_mode: Choice = Field(
        description="Remediation Mode",
        choices=[
            ("report_only", "Report Only"),
            ("auto_fix", "Auto-Fix Minor Issues"),
            ("manual_approval", "Manual Approval Required")
        ],
        default="report_only"
    )


@workflow("Device Health Check", target=Target.CREATE)
def device_health_check() -> StepList:
    return begin
        >> store_process_subscription(Target.CREATE)
        >> select_target_devices
        >> execute_health_checks
        >> analyze_results
        >> generate_health_report
        >> apply_remediation
        >> done


def initial_input_form_generator(subscription_id: UUIDstr) -> FormPage:
    """Generate health check form"""
    return HealthCheckForm


def select_target_devices(subscription: DeviceInactive) -> DeviceProvisioning:
    """Select devices for health check based on criteria"""
    subscription = DeviceProvisioning.from_other_lifecycle(
        subscription, SubscriptionLifecycle.PROVISIONING
    )
    
    target_devices = []
    
    if subscription.device_selection == "single_device":
        device = netbox.get_device(subscription.device_id)
        target_devices = [device]
    
    elif subscription.device_selection == "site_devices":
        devices = netbox.get_devices_by_site(subscription.site_name)
        target_devices = devices
    
    elif subscription.device_selection == "device_type":
        devices = netbox.get_devices_by_type(subscription.device_type_filter)
        target_devices = devices
        
    elif subscription.device_selection == "all_devices":
        devices = netbox.get_all_devices(status="active")
        target_devices = devices
    
    subscription.target_devices = target_devices
    subscription.device_count = len(target_devices)
    
    return subscription


def execute_health_checks(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Execute health checks on target devices"""
    
    callback_route = f"/api/workflows/device/health/{subscription.subscription_id}/results"
    
    # Build inventory from target devices
    inventory_hosts = []
    for device in subscription.target_devices:
        inventory_hosts.append(device["primary_ip4"] or device["name"])
    
    inventory = "\n".join(inventory_hosts) + "\n"
    
    extra_vars = {
        "check_types": subscription.check_types,
        "devices": subscription.target_devices,
        "remediation_mode": subscription.remediation_mode
    }
    
    execute_playbook(
        playbook_name="device_health_check.yaml",
        callback_route=callback_route,
        inventory=inventory,
        extra_vars=extra_vars
    )
    
    return subscription


def analyze_results(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Analyze health check results and categorize issues"""
    
    # Health check results would come from Ansible callback
    # Simulating results structure for now
    health_results = {
        "overall_status": "warning",
        "devices_checked": subscription.device_count,
        "devices_healthy": 0,
        "devices_warning": 0,
        "devices_critical": 0,
        "device_results": []
    }
    
    critical_issues = []
    warning_issues = []
    recommendations = []
    
    for device in subscription.target_devices:
        device_result = {
            "device_name": device["name"],
            "device_ip": device.get("primary_ip4"),
            "overall_health": "healthy",  # Would be determined by checks
            "hardware_status": "ok",
            "software_status": "ok", 
            "interface_status": "warning",
            "protocol_status": "ok",
            "performance_status": "ok",
            "security_status": "warning",
            "configuration_status": "ok",
            "issues": [],
            "recommendations": []
        }
        
        # Categorize device health
        if "critical" in [device_result["hardware_status"], device_result["software_status"]]:
            device_result["overall_health"] = "critical"
            health_results["devices_critical"] += 1
        elif "warning" in [device_result["interface_status"], device_result["security_status"]]:
            device_result["overall_health"] = "warning"
            health_results["devices_warning"] += 1
        else:
            health_results["devices_healthy"] += 1
        
        health_results["device_results"].append(device_result)
    
    # Determine overall health
    if health_results["devices_critical"] > 0:
        health_results["overall_status"] = "critical"
    elif health_results["devices_warning"] > 0:
        health_results["overall_status"] = "warning"
    else:
        health_results["overall_status"] = "healthy"
    
    subscription.health_results = health_results
    
    return subscription


def generate_health_report(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Generate comprehensive health report"""
    
    if not subscription.generate_report:
        return subscription
    
    report_data = {
        "report_id": f"health-{subscription.subscription_id}",
        "generated_at": subscription.created_at.isoformat(),
        "summary": subscription.health_results,
        "device_selection": subscription.device_selection,
        "check_types": subscription.check_types,
        "remediation_recommendations": []
    }
    
    # Generate remediation recommendations
    for device_result in subscription.health_results["device_results"]:
        if device_result["overall_health"] != "healthy":
            recommendations = []
            
            if device_result["interface_status"] == "warning":
                recommendations.append("Check interface configurations and cable connections")
            
            if device_result["security_status"] == "warning":
                recommendations.append("Update security policies and access controls")
                
            if device_result["software_status"] == "warning":
                recommendations.append("Schedule firmware update")
            
            report_data["remediation_recommendations"].extend(recommendations)
    
    # Store report in database or file system
    subscription.health_report = report_data
    subscription.report_generated = True
    
    return subscription


def apply_remediation(subscription: DeviceProvisioning) -> DeviceProvisioning:
    """Apply automated remediation based on mode"""
    
    if subscription.remediation_mode == "report_only":
        return subscription
    
    auto_fix_issues = []
    manual_issues = []
    
    # Categorize issues for remediation
    for device_result in subscription.health_results["device_results"]:
        for issue in device_result.get("issues", []):
            if issue["severity"] == "low" and issue["auto_fixable"]:
                auto_fix_issues.append(issue)
            else:
                manual_issues.append(issue)
    
    # Apply auto-fixes if enabled
    if subscription.remediation_mode in ["auto_fix", "manual_approval"] and auto_fix_issues:
        callback_route = f"/api/workflows/device/health/{subscription.subscription_id}/remediate"
        
        extra_vars = {
            "auto_fix_issues": auto_fix_issues,
            "approval_required": subscription.remediation_mode == "manual_approval"
        }
        
        execute_playbook(
            playbook_name="device_remediation.yaml",
            callback_route=callback_route,
            inventory="\n".join([d["primary_ip4"] for d in subscription.target_devices]) + "\n",
            extra_vars=extra_vars
        )
    
    subscription.remediation_applied = len(auto_fix_issues)
    subscription.manual_intervention_required = len(manual_issues)
    
    return subscription
