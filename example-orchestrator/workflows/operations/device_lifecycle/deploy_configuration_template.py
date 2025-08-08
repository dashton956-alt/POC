"""
Deploy Configuration Template Workflow
Apply standardized device configurations using templates
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

from products.product_types.device import DeviceInactive, DeviceProvisioning
from services.netbox import netbox
from services.catalyst_center import catalyst_center_client
from services.lso_client import execute_playbook
from services.api_manager import api_manager
from services.device_connector import device_connector
from workflows.shared import device_selector


class ConfigTemplateForm(FormPage):
    """Configuration Template Deployment Form"""
    
    # Device Selection
    target_devices: List[str] = Field(
        description="Target Devices",
        min_items=1
    )
    
    # Template Selection
    template_source: Choice = Field(
        description="Template Source",
        choices=[
            ("local", "Local Jinja2 Templates"),
            ("catalyst_center", "Catalyst Center Templates"),
            ("custom", "Custom Configuration")
        ]
    )
    
    template_name: str = Field(
        description="Template Name",
        min_length=1
    )
    
    template_category: Choice = Field(
        description="Template Category",
        choices=[
            ("interface", "Interface Configuration"),
            ("routing", "Routing Configuration"),
            ("switching", "Switching Configuration"),
            ("security", "Security Configuration"),
            ("qos", "Quality of Service"),
            ("monitoring", "Monitoring Configuration"),
            ("system", "System Configuration"),
            ("custom", "Custom Configuration")
        ]
    )
    
    # Template Variables
    template_variables: Dict[str, Any] = Field(
        description="Template Variables (JSON format)",
        default={}
    )
    
    # Deployment Options
    deployment_strategy: Choice = Field(
        description="Deployment Strategy",
        choices=[
            ("immediate", "Immediate Deployment"),
            ("staged", "Staged Deployment"),
            ("scheduled", "Scheduled Deployment"),
            ("validation_only", "Validation Only")
        ],
        default="staged"
    )
    
    backup_before_deploy: bool = Field(
        description="Backup Configuration Before Deployment",
        default=True
    )
    
    validate_before_commit: bool = Field(
        description="Validate Configuration Before Commit",
        default=True
    )
    
    rollback_on_failure: bool = Field(
        description="Automatic Rollback on Failure",
        default=True
    )
    
    # Validation Options
    dry_run: bool = Field(
        description="Perform Dry Run (Generate Only)",
        default=False
    )
    
    compliance_check: bool = Field(
        description="Run Compliance Check After Deployment",
        default=True
    )


@workflow("Deploy Configuration Template", target=Target.CREATE)
def deploy_configuration_template(subscription: DeviceInactive) -> State:
    """Deploy configuration template workflow"""
    return (
        begin
        >> store_process_subscription(subscription)
        >> validate_template_and_devices
        >> generate_device_configurations
        >> validate_generated_configurations
        >> backup_current_configurations
        >> deploy_configurations
        >> verify_deployment
        >> run_compliance_check
        >> update_device_records
        >> done
    )


@deploy_configuration_template.step("Validate Template and Devices")
def validate_template_and_devices(subscription: DeviceProvisioning) -> State:
    """Validate template exists and devices are compatible"""
    
    validated_devices = []
    template_info = {}
    
    # Validate template based on source
    if subscription.template_source == "catalyst_center":
        # Validate Catalyst Center template
        template_info = catalyst_center_client.get_template(subscription.template_name)
        if not template_info:
            raise ValueError(f"Catalyst Center template '{subscription.template_name}' not found")
            
    elif subscription.template_source == "local":
        # Validate local Jinja2 template
        template_result = execute_playbook(
            "ansible/operations/validate_template.yaml",
            extra_vars={
                "template_name": subscription.template_name,
                "template_category": subscription.template_category,
                "template_source": "local"
            }
        )
        
        if not template_result.get("success"):
            raise ValueError(f"Local template validation failed: {template_result.get('error')}")
        
        template_info = template_result.get("template_info")
    
    # Validate each target device
    for device_id in subscription.target_devices:
        device_info = netbox.get_device(device_id)
        if not device_info:
            raise ValueError(f"Device {device_id} not found in NetBox")
        
        # Check device compatibility with template
        device_platform = device_info.get("platform", {}).get("slug")
        device_vendor = device_info.get("device_type", {}).get("manufacturer", {}).get("slug")
        
        # Validate platform compatibility
        compatible_platforms = template_info.get("compatible_platforms", [])
        if compatible_platforms and device_platform not in compatible_platforms:
            raise ValueError(f"Device {device_id} platform '{device_platform}' not compatible with template")
        
        validated_devices.append({
            "device_id": device_id,
            "device_name": device_info.get("name"),
            "device_ip": device_info.get("primary_ip4", {}).get("address", "").split("/")[0],
            "platform": device_platform,
            "vendor": device_vendor,
            "status": device_info.get("status", {}).get("value")
        })
    
    subscription.validated_devices = validated_devices
    subscription.template_info = template_info
    subscription.total_devices = len(validated_devices)
    
    return subscription


@deploy_configuration_template.step("Generate Device Configurations")
def generate_device_configurations(subscription: DeviceProvisioning) -> State:
    """Generate configuration for each target device"""
    
    device_configurations = {}
    
    for device in subscription.validated_devices:
        # Prepare device-specific variables
        device_vars = {
            **subscription.template_variables,
            "device_id": device["device_id"],
            "device_name": device["device_name"],
            "device_ip": device["device_ip"],
            "device_platform": device["platform"],
            "device_vendor": device["vendor"]
        }
        
        if subscription.template_source == "catalyst_center":
            # Generate using Catalyst Center
            config_result = catalyst_center_client.generate_template_config(
                template_id=subscription.template_info["id"],
                device_id=device["device_id"],
                variables=device_vars
            )
            
        else:
            # Generate using Ansible/Jinja2
            config_result = execute_playbook(
                "ansible/operations/generate_device_config.yaml",
                extra_vars={
                    "template_name": subscription.template_name,
                    "template_category": subscription.template_category,
                    "device_vars": device_vars,
                    "output_format": device["platform"]
                }
            )
        
        if not config_result.get("success"):
            raise RuntimeError(f"Failed to generate configuration for device {device['device_name']}: {config_result.get('error')}")
        
        device_configurations[device["device_id"]] = {
            "configuration": config_result.get("configuration"),
            "checksum": config_result.get("checksum"),
            "line_count": config_result.get("line_count", 0),
            "generated_at": config_result.get("timestamp")
        }
    
    subscription.device_configurations = device_configurations
    subscription.configurations_generated = True
    
    return subscription


@deploy_configuration_template.step("Validate Generated Configurations")
def validate_generated_configurations(subscription: DeviceProvisioning) -> State:
    """Validate generated configurations for syntax and compliance"""
    
    validation_results = {}
    
    for device in subscription.validated_devices:
        device_id = device["device_id"]
        config_data = subscription.device_configurations[device_id]
        
        # Validate configuration syntax
        validation_result = execute_playbook(
            "ansible/operations/validate_config_syntax.yaml",
            extra_vars={
                "device_platform": device["platform"],
                "configuration": config_data["configuration"],
                "validation_level": "strict"
            }
        )
        
        validation_results[device_id] = {
            "syntax_valid": validation_result.get("syntax_valid", False),
            "syntax_errors": validation_result.get("syntax_errors", []),
            "warnings": validation_result.get("warnings", []),
            "line_errors": validation_result.get("line_errors", {})
        }
        
        if not validation_result.get("syntax_valid"):
            raise RuntimeError(f"Configuration validation failed for device {device['device_name']}: {validation_result.get('syntax_errors')}")
    
    subscription.validation_results = validation_results
    subscription.configurations_validated = True
    
    # Stop here if dry run
    if subscription.dry_run:
        subscription.deployment_status = "dry_run_completed"
        return subscription
    
    return subscription


@deploy_configuration_template.step("Backup Current Configurations")
def backup_current_configurations(subscription: DeviceProvisioning) -> State:
    """Backup current device configurations before deployment"""
    
    if not subscription.backup_before_deploy:
        subscription.backup_skipped = True
        return subscription
    
    backup_results = {}
    
    for device in subscription.validated_devices:
        device_id = device["device_id"]
        
        # Backup current configuration
        backup_result = execute_playbook(
            "ansible/operations/backup_device_config.yaml",
            extra_vars={
                "device_ip": device["device_ip"],
                "device_platform": device["platform"],
                "backup_location": f"backups/pre_template_deploy_{subscription.subscription_id}",
                "include_startup": True,
                "include_running": True
            }
        )
        
        backup_results[device_id] = {
            "backup_successful": backup_result.get("success", False),
            "backup_id": backup_result.get("backup_id"),
            "backup_path": backup_result.get("backup_path"),
            "backup_timestamp": backup_result.get("timestamp"),
            "error": backup_result.get("error")
        }
        
        if not backup_result.get("success") and subscription.rollback_on_failure:
            raise RuntimeError(f"Failed to backup device {device['device_name']}: {backup_result.get('error')}")
    
    subscription.backup_results = backup_results
    subscription.configurations_backed_up = True
    
    return subscription


@deploy_configuration_template.step("Deploy Configurations")
def deploy_configurations(subscription: DeviceProvisioning) -> State:
    """Deploy configurations to target devices"""
    
    deployment_results = {}
    successful_deployments = 0
    
    for device in subscription.validated_devices:
        device_id = device["device_id"]
        config_data = subscription.device_configurations[device_id]
        
        try:
            # Deploy configuration
            deploy_result = execute_playbook(
                "ansible/operations/deploy_device_config.yaml",
                extra_vars={
                    "device_ip": device["device_ip"],
                    "device_platform": device["platform"],
                    "configuration": config_data["configuration"],
                    "validate_before_commit": subscription.validate_before_commit,
                    "commit_changes": True,
                    "deployment_strategy": subscription.deployment_strategy
                }
            )
            
            deployment_results[device_id] = {
                "deployment_successful": deploy_result.get("success", False),
                "deployment_id": deploy_result.get("deployment_id"),
                "deployment_timestamp": deploy_result.get("timestamp"),
                "changes_applied": deploy_result.get("changes_applied", 0),
                "error": deploy_result.get("error")
            }
            
            if deploy_result.get("success"):
                successful_deployments += 1
            else:
                # Handle deployment failure
                if subscription.rollback_on_failure:
                    # Attempt rollback
                    rollback_result = execute_playbook(
                        "ansible/operations/rollback_device_config.yaml",
                        extra_vars={
                            "device_ip": device["device_ip"],
                            "device_platform": device["platform"],
                            "backup_id": subscription.backup_results[device_id]["backup_id"]
                        }
                    )
                    deployment_results[device_id]["rollback_attempted"] = True
                    deployment_results[device_id]["rollback_successful"] = rollback_result.get("success", False)
                
        except Exception as e:
            deployment_results[device_id] = {
                "deployment_successful": False,
                "error": str(e),
                "exception_occurred": True
            }
    
    subscription.deployment_results = deployment_results
    subscription.successful_deployments = successful_deployments
    subscription.deployment_completed = True
    
    # Check if any deployments failed
    if successful_deployments == 0:
        raise RuntimeError("All configuration deployments failed")
    elif successful_deployments < len(subscription.validated_devices):
        subscription.partial_deployment = True
    
    return subscription


@deploy_configuration_template.step("Verify Deployment")
def verify_deployment(subscription: DeviceProvisioning) -> State:
    """Verify deployed configurations"""
    
    verification_results = {}
    
    for device in subscription.validated_devices:
        device_id = device["device_id"]
        
        # Skip verification if deployment failed
        if not subscription.deployment_results[device_id].get("deployment_successful"):
            continue
        
        # Verify configuration was applied
        verify_result = execute_playbook(
            "ansible/operations/verify_config_deployment.yaml",
            extra_vars={
                "device_ip": device["device_ip"],
                "device_platform": device["platform"],
                "expected_config": subscription.device_configurations[device_id]["configuration"],
                "verify_connectivity": True,
                "verify_services": True
            }
        )
        
        verification_results[device_id] = {
            "verification_successful": verify_result.get("success", False),
            "config_matches": verify_result.get("config_matches", False),
            "connectivity_verified": verify_result.get("connectivity_verified", False),
            "services_verified": verify_result.get("services_verified", {}),
            "verification_errors": verify_result.get("errors", [])
        }
    
    subscription.verification_results = verification_results
    subscription.deployment_verified = True
    
    return subscription


@deploy_configuration_template.step("Run Compliance Check")
def run_compliance_check(subscription: DeviceProvisioning) -> State:
    """Run compliance check on deployed configurations"""
    
    if not subscription.compliance_check:
        subscription.compliance_skipped = True
        return subscription
    
    compliance_results = {}
    
    for device in subscription.validated_devices:
        device_id = device["device_id"]
        
        # Skip compliance check if deployment failed
        if not subscription.deployment_results[device_id].get("deployment_successful"):
            continue
        
        # Run compliance check
        compliance_result = execute_playbook(
            "ansible/operations/compliance_check.yaml",
            extra_vars={
                "device_ip": device["device_ip"],
                "device_platform": device["platform"],
                "compliance_policies": ["security_baseline", "configuration_standards"],
                "template_category": subscription.template_category
            }
        )
        
        compliance_results[device_id] = {
            "compliance_score": compliance_result.get("compliance_score", 0),
            "policy_violations": compliance_result.get("policy_violations", []),
            "security_issues": compliance_result.get("security_issues", []),
            "recommendations": compliance_result.get("recommendations", [])
        }
    
    subscription.compliance_results = compliance_results
    subscription.compliance_check_completed = True
    
    return subscription


@deploy_configuration_template.step("Update Device Records")
def update_device_records(subscription: DeviceProvisioning) -> State:
    """Update device records with deployment information"""
    
    for device in subscription.validated_devices:
        device_id = device["device_id"]
        deployment_result = subscription.deployment_results[device_id]
        
        if deployment_result.get("deployment_successful"):
            # Update NetBox device record
            netbox_update = {
                "comments": f"Template deployed: {subscription.template_name} on {deployment_result['deployment_timestamp']}",
                "custom_fields": {
                    "last_template_deployment": subscription.template_name,
                    "template_deployment_timestamp": deployment_result["deployment_timestamp"],
                    "config_checksum": subscription.device_configurations[device_id]["checksum"]
                }
            }
            
            try:
                netbox.update_device(device_id, netbox_update)
            except Exception as e:
                # Log error but don't fail workflow
                subscription.netbox_errors = subscription.netbox_errors or {}
                subscription.netbox_errors[device_id] = str(e)
    
    subscription.device_records_updated = True
    
    return subscription
