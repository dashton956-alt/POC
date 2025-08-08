"""
Intent-Based Workflow Group Registration  
Register all intent-based network automation workflows
"""

from workflows.intent_based.service_orchestration.l3vpn_service import deploy_l3vpn_service
from workflows.intent_based.wireless_management.mist_wireless_service import deploy_wireless_service

# Service Orchestration Workflows
SERVICE_ORCHESTRATION_WORKFLOWS = [
    {
        "workflow": deploy_l3vpn_service,
        "name": "Deploy L3VPN Service", 
        "description": "Intent-based end-to-end L3VPN service provisioning with AI-driven optimization",
        "category": "Service Orchestration",
        "tags": ["l3vpn", "mpls", "service", "bgp", "intent_based", "ai_optimized"],
        "complexity": "very_high",
        "estimated_duration": "20-45 minutes",
        "service_type": "network_service",
        "automation_level": "fully_automated",
        "rollback_supported": True
    }
]

# Wireless Management Workflows
WIRELESS_MANAGEMENT_WORKFLOWS = [
    {
        "workflow": deploy_wireless_service,
        "name": "Deploy Wireless Network Service",
        "description": "Intent-based wireless network provisioning with Mist AI optimization",
        "category": "Wireless Management", 
        "tags": ["wireless", "wifi", "mist", "ai_optimization", "intent_based", "coverage"],
        "complexity": "high",
        "estimated_duration": "15-30 minutes",
        "service_type": "wireless_service", 
        "automation_level": "ai_assisted",
        "rollback_supported": True
    }
]

# Security & Access Control Workflows
SECURITY_ACCESS_WORKFLOWS = [
    # NAC, 802.1x, dynamic VLAN assignment workflows would be registered here
]

# OSS Integration Workflows
OSS_INTEGRATION_WORKFLOWS = [
    # Catalyst Center, Mist, ServiceNow integration workflows would be registered here
]

# Compliance & Governance Workflows  
COMPLIANCE_GOVERNANCE_WORKFLOWS = [
    # Configuration compliance, security auditing workflows would be registered here
]

# Combine all intent-based workflows
ALL_INTENT_BASED_WORKFLOWS = (
    SERVICE_ORCHESTRATION_WORKFLOWS +
    WIRELESS_MANAGEMENT_WORKFLOWS +
    SECURITY_ACCESS_WORKFLOWS +
    OSS_INTEGRATION_WORKFLOWS +
    COMPLIANCE_GOVERNANCE_WORKFLOWS
)


def register_intent_based_workflows():
    """Register all intent-based workflows with the orchestrator"""
    registered_workflows = []
    
    for workflow_config in ALL_INTENT_BASED_WORKFLOWS:
        try:
            # Register workflow with orchestrator
            workflow_registration = {
                "workflow_function": workflow_config["workflow"],
                "metadata": {
                    "name": workflow_config["name"],
                    "description": workflow_config["description"], 
                    "category": workflow_config["category"],
                    "group": "Intent-Based",
                    "tags": workflow_config["tags"],
                    "complexity": workflow_config["complexity"],
                    "estimated_duration": workflow_config["estimated_duration"],
                    "workflow_type": "intent_based",
                    "service_type": workflow_config.get("service_type", "unknown"),
                    "automation_level": workflow_config.get("automation_level", "manual"),
                    "rollback_supported": workflow_config.get("rollback_supported", False),
                    "ai_enabled": "ai" in " ".join(workflow_config["tags"]),
                    "multi_vendor": True  # Intent-based workflows are typically multi-vendor
                }
            }
            
            registered_workflows.append(workflow_registration)
            print(f"🚀 Registered intent-based workflow: {workflow_config['name']}")
            
        except Exception as e:
            print(f"❌ Failed to register workflow {workflow_config['name']}: {str(e)}")
    
    print(f"\n🎯 Intent-Based Workflow Registration Summary:")
    print(f"Total workflows registered: {len(registered_workflows)}")
    print(f"Service Orchestration: {len(SERVICE_ORCHESTRATION_WORKFLOWS)}")
    print(f"Wireless Management: {len(WIRELESS_MANAGEMENT_WORKFLOWS)}")
    print(f"Security & Access Control: {len(SECURITY_ACCESS_WORKFLOWS)}")
    print(f"OSS Integration: {len(OSS_INTEGRATION_WORKFLOWS)}")
    print(f"Compliance & Governance: {len(COMPLIANCE_GOVERNANCE_WORKFLOWS)}")
    
    return registered_workflows


# Workflow categories for UI organization  
INTENT_BASED_WORKFLOW_CATEGORIES = [
    {
        "name": "Service Orchestration",
        "description": "End-to-end network service provisioning with intent-based automation",
        "icon": "sitemap",
        "color": "primary",
        "ai_enabled": True,
        "workflows": [w["name"] for w in SERVICE_ORCHESTRATION_WORKFLOWS],
        "features": ["AI-Driven Design", "Multi-Vendor", "Full Automation", "SLA Monitoring"]
    },
    {
        "name": "Wireless Management", 
        "description": "Intent-based wireless network design and optimization",
        "icon": "wifi",
        "color": "info",
        "ai_enabled": True,
        "workflows": [w["name"] for w in WIRELESS_MANAGEMENT_WORKFLOWS],
        "features": ["AI RF Optimization", "Mist Integration", "Coverage Analysis", "User Experience Focus"]
    },
    {
        "name": "Security & Access Control",
        "description": "Zero-trust security and network access control automation", 
        "icon": "shield-alt",
        "color": "warning",
        "ai_enabled": False,
        "workflows": [w["name"] for w in SECURITY_ACCESS_WORKFLOWS],
        "features": ["Zero Trust", "Dynamic Policies", "Identity Integration", "Micro-Segmentation"]
    },
    {
        "name": "OSS Integration",
        "description": "Seamless integration with network management systems",
        "icon": "plug",
        "color": "success", 
        "ai_enabled": True,
        "workflows": [w["name"] for w in OSS_INTEGRATION_WORKFLOWS],
        "features": ["Catalyst Center", "Mist Cloud", "ServiceNow", "Multi-System Sync"]
    },
    {
        "name": "Compliance & Governance",
        "description": "Automated compliance monitoring and policy enforcement",
        "icon": "clipboard-check",
        "color": "secondary",
        "ai_enabled": True, 
        "workflows": [w["name"] for w in COMPLIANCE_GOVERNANCE_WORKFLOWS],
        "features": ["Policy Automation", "Audit Trail", "Drift Detection", "Remediation"]
    }
]


# Intent-based workflow capabilities
INTENT_BASED_CAPABILITIES = {
    "ai_optimization": {
        "description": "AI-driven network design and optimization",
        "workflows": [w for w in ALL_INTENT_BASED_WORKFLOWS if "ai" in " ".join(w["tags"])],
        "benefits": ["Optimal Performance", "Predictive Analytics", "Self-Healing", "Continuous Learning"]
    },
    "multi_vendor_support": {
        "description": "Vendor-agnostic service provisioning",
        "workflows": ALL_INTENT_BASED_WORKFLOWS,
        "benefits": ["Vendor Independence", "Best-of-Breed", "Cost Optimization", "Future-Proof"]
    },
    "service_assurance": {
        "description": "End-to-end service monitoring and SLA management",
        "workflows": [w for w in ALL_INTENT_BASED_WORKFLOWS if w.get("rollback_supported")],
        "benefits": ["SLA Compliance", "Proactive Monitoring", "Automatic Remediation", "Performance Analytics"]
    },
    "zero_touch_provisioning": {
        "description": "Fully automated service provisioning with minimal human intervention", 
        "workflows": [w for w in ALL_INTENT_BASED_WORKFLOWS if w.get("automation_level") == "fully_automated"],
        "benefits": ["Reduced OPEX", "Faster Deployment", "Consistent Quality", "Error Reduction"]
    }
}
